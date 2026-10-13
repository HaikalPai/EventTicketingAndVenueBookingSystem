"""Event ticketing demonstration API. Run: uvicorn backend.main:app --reload"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import quote
import jwt
import httpx
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import create_engine, ForeignKey, String, Integer, DateTime, CheckConstraint, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker, Session
from pydantic import BaseModel, ConfigDict, EmailStr, Field
import hashlib, hmac, secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_URL = os.getenv('DATABASE_URL',f'sqlite:///{ROOT / "ticketing.db"}')
SECRET = os.getenv('JWT_SECRET','DEVELOPMENT-ONLY-CHANGE-ME')
engine = create_engine(DB_URL, connect_args={'check_same_thread':False} if DB_URL.startswith('sqlite') else {})
SessionLocal = sessionmaker(bind=engine)
class PasswordHash:
    def hash(self,password):
        salt=secrets.token_hex(16)
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),260000).hex()
        return 'pbkdf2_sha256$260000$'+salt+'$'+digest
    def verify(self,password,stored):
        try:
            algo,n,salt,expected=stored.split('$')
            if algo!='pbkdf2_sha256':return False
            computed=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(n)).hex()
            return hmac.compare_digest(computed,expected)
        except (ValueError,TypeError):return False
password_hash=PasswordHash()

class Base(DeclarativeBase): pass
class User(Base):
    __tablename__='users'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default='customer')
    __table_args__=(CheckConstraint("role IN ('admin','organiser','staff','customer')"),)
class Venue(Base):
    __tablename__='venues'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(140), unique=True)
    location: Mapped[str] = mapped_column(String(250))
    capacity: Mapped[int] = mapped_column(Integer)
    __table_args__=(CheckConstraint('capacity > 0'),)
class Event(Base):
    __tablename__='events'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180))
    description: Mapped[str] = mapped_column(String(1200), default='')
    venue_id: Mapped[int] = mapped_column(ForeignKey('venues.id'))
    organiser_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    starts_at: Mapped[datetime] = mapped_column(DateTime)
    ticket_limit: Mapped[int] = mapped_column(Integer)
    __table_args__=(CheckConstraint('ticket_limit > 0'),)
class Booking(Base):
    __tablename__='bookings'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    event_id: Mapped[int] = mapped_column(ForeignKey('events.id'))
    quantity: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default='confirmed')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    __table_args__=(CheckConstraint('quantity > 0'),CheckConstraint("status IN ('confirmed','cancelled')"),)
Base.metadata.create_all(engine)

class UserIn(BaseModel):
    name: str = Field(min_length=2,max_length=120)
    email: EmailStr
    password: str = Field(min_length=8)
class LoginIn(BaseModel): email: EmailStr; password: str
class VenueIn(BaseModel):
    name: str = Field(min_length=2)
    location: str = Field(min_length=2)
    capacity: int = Field(gt=0)
class EventIn(BaseModel):
    name: str = Field(min_length=2)
    description: str = ''
    venue_id: int
    starts_at: datetime
    ticket_limit: int = Field(gt=0)
class BookingIn(BaseModel): event_id: int; quantity: int = Field(gt=0,le=20)
class BookingEdit(BaseModel): quantity: Optional[int] = Field(default=None,gt=0,le=20)
class UserOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; name:str; email:EmailStr; role:str
class VenueOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; name:str; location:str; capacity:int
class EventOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; name:str; description:str; venue_id:int; organiser_id:int; starts_at:datetime; ticket_limit:int
class BookingOut(BaseModel):
    model_config=ConfigDict(from_attributes=True)
    id:int; user_id:int; event_id:int; quantity:int; status:str; created_at:datetime

def db_session():
    with SessionLocal() as db: yield db

oauth_scheme = OAuth2PasswordBearer(tokenUrl='/auth/login')
def current_user(token:str=Depends(oauth_scheme),db:Session=Depends(db_session)):
    try:
        payload=jwt.decode(token,SECRET,algorithms=['HS256'])
        uid=int(payload['sub'])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(401,'Invalid or expired access token')
    user=db.get(User,uid)
    if not user: raise HTTPException(401,'User no longer exists')
    return user

def manager(user:User=Depends(current_user)):
    if user.role not in ('admin','organiser','staff'): raise HTTPException(403,'Management role required')
    return user

def admin(user:User=Depends(current_user)):
    if user.role!='admin': raise HTTPException(403,'Administrator required')
    return user

def fail_if_missing(item,name):
    if not item: raise HTTPException(404,f'{name} not found')
    return item

def availability(db,event_id:int, exclude_booking_id:int|None=None):
    event=fail_if_missing(db.get(Event,event_id),'Event')
    q=select(func.coalesce(func.sum(Booking.quantity),0)).where(Booking.event_id==event_id,Booking.status=='confirmed')
    if exclude_booking_id is not None:q=q.where(Booking.id!=exclude_booking_id)
    sold=db.scalar(q) or 0
    return min(event.ticket_limit,fail_if_missing(db.get(Venue,event.venue_id),'Venue').capacity)-sold

app=FastAPI(title='Event Ticketing and Venue Booking API',version='1.0.0',description='SWC3633 group project reference implementation')
app.add_middleware(CORSMiddleware,allow_origins=['http://localhost:8000','http://127.0.0.1:8000'],allow_methods=['*'],allow_headers=['*'])

@app.get('/')
def landing():return RedirectResponse('/frontend/customer.html')
@app.get('/frontend/{filename}')
def frontend(filename:str):
    if filename not in ('customer.html','organiser.html','staff.html','app.js','style.css'):raise HTTPException(404,'Not found')
    return FileResponse(ROOT/'frontend'/filename)
@app.post('/auth/register',response_model=UserOut,status_code=201)
def register(data:UserIn,db:Session=Depends(db_session)):
    if db.scalar(select(User).where(User.email==str(data.email).lower())): raise HTTPException(409,'Email already exists')
    u=User(name=data.name,email=str(data.email).lower(),password_hash=password_hash.hash(data.password),role='customer')
    db.add(u);db.commit();db.refresh(u);return u
@app.post('/auth/login')
def login(data:LoginIn,db:Session=Depends(db_session)):
    u=db.scalar(select(User).where(User.email==str(data.email).lower()))
    if not u or not password_hash.verify(data.password,u.password_hash):raise HTTPException(401,'Invalid credentials')
    token=jwt.encode({'sub':str(u.id),'exp':datetime.now(timezone.utc)+timedelta(hours=6)},SECRET,algorithm='HS256')
    return {'access_token':token,'token_type':'bearer','role':u.role,'name':u.name}
@app.get('/users',response_model=list[UserOut])
def users(db:Session=Depends(db_session),_:User=Depends(admin)):return list(db.scalars(select(User).order_by(User.id)))
@app.get('/users/me',response_model=UserOut)
def me(u:User=Depends(current_user)):return u
@app.get('/users/{id}',response_model=UserOut)
def user_detail(id:int,db:Session=Depends(db_session),u:User=Depends(current_user)):
    if u.role!='admin' and u.id!=id:raise HTTPException(403,'Not permitted')
    return fail_if_missing(db.get(User,id),'User')
@app.delete('/users/{id}',status_code=204)
def user_delete(id:int,db:Session=Depends(db_session),u:User=Depends(admin)):
    if u.id==id:raise HTTPException(400,'Cannot delete own admin account')
    target=fail_if_missing(db.get(User,id),'User')
    if db.scalar(select(Booking.id).where(Booking.user_id==id).limit(1)) or db.scalar(select(Event.id).where(Event.organiser_id==id).limit(1)):
        raise HTTPException(409,'User has associated records')
    db.delete(target);db.commit()
@app.get('/venues',response_model=list[VenueOut])
def venues(db:Session=Depends(db_session)):return list(db.scalars(select(Venue).order_by(Venue.id)))
@app.get('/venues/{id}',response_model=VenueOut)
def venue_detail(id:int,db:Session=Depends(db_session)):return fail_if_missing(db.get(Venue,id),'Venue')
@app.post('/venues',response_model=VenueOut,status_code=201)
def venue_create(data:VenueIn,db:Session=Depends(db_session),_:User=Depends(manager)):
    if db.scalar(select(Venue).where(Venue.name==data.name)):raise HTTPException(409,'Venue name already exists')
    v=Venue(**data.model_dump());db.add(v);db.commit();db.refresh(v);return v
@app.put('/venues/{id}',response_model=VenueOut)
def venue_update(id:int,data:VenueIn,db:Session=Depends(db_session),_:User=Depends(manager)):
    v=fail_if_missing(db.get(Venue,id),'Venue')
    for k,val in data.model_dump().items():setattr(v,k,val)
    db.commit();db.refresh(v);return v
@app.delete('/venues/{id}',status_code=204)
def venue_delete(id:int,db:Session=Depends(db_session),_:User=Depends(manager)):
    v=fail_if_missing(db.get(Venue,id),'Venue')
    if db.scalar(select(Event.id).where(Event.venue_id==id).limit(1)):raise HTTPException(409,'Venue has events')
    db.delete(v);db.commit()
@app.get('/events',response_model=list[EventOut])
def events(search:str='',skip:int=Query(0,ge=0),limit:int=Query(20,ge=1,le=100),db:Session=Depends(db_session)):
    q=select(Event)
    if search:q=q.where(Event.name.ilike(f'%{search}%'))
    return list(db.scalars(q.order_by(Event.starts_at).offset(skip).limit(limit)))
@app.get('/events/{id}',response_model=EventOut)
def event_detail(id:int,db:Session=Depends(db_session)):return fail_if_missing(db.get(Event,id),'Event')
@app.get('/events/{id}/availability')
def event_available(id:int,db:Session=Depends(db_session)):return {'event_id':id,'remaining':availability(db,id)}
@app.post('/events',response_model=EventOut,status_code=201)
def event_create(data:EventIn,db:Session=Depends(db_session),u:User=Depends(manager)):
    venue=fail_if_missing(db.get(Venue,data.venue_id),'Venue')
    if data.ticket_limit>venue.capacity:raise HTTPException(422,'Ticket limit exceeds venue capacity')
    e=Event(**data.model_dump(),organiser_id=u.id);db.add(e);db.commit();db.refresh(e);return e
@app.put('/events/{id}',response_model=EventOut)
def event_update(id:int,data:EventIn,db:Session=Depends(db_session),u:User=Depends(manager)):
    e=fail_if_missing(db.get(Event,id),'Event')
    if u.role!='admin' and e.organiser_id!=u.id:raise HTTPException(403,'Not event owner')
    venue=fail_if_missing(db.get(Venue,data.venue_id),'Venue')
    sold=e.ticket_limit-availability(db,id)
    if data.ticket_limit>venue.capacity or data.ticket_limit<sold:raise HTTPException(422,'Invalid capacity/ticket limit')
    for k,val in data.model_dump().items():setattr(e,k,val)
    db.commit();db.refresh(e);return e
@app.delete('/events/{id}',status_code=204)
def event_delete(id:int,db:Session=Depends(db_session),u:User=Depends(manager)):
    e=fail_if_missing(db.get(Event,id),'Event')
    if u.role!='admin' and e.organiser_id!=u.id:raise HTTPException(403,'Not event owner')
    if db.scalar(select(Booking.id).where(Booking.event_id==id).limit(1)):raise HTTPException(409,'Event has bookings')
    db.delete(e);db.commit()
@app.get('/bookings',response_model=list[BookingOut])
def bookings(db:Session=Depends(db_session),u:User=Depends(current_user)):
    q=select(Booking)
    if u.role=='customer':q=q.where(Booking.user_id==u.id)
    return list(db.scalars(q.order_by(Booking.id.desc())))
@app.get('/bookings/{id}',response_model=BookingOut)
def booking_detail(id:int,db:Session=Depends(db_session),u:User=Depends(current_user)):
    b=fail_if_missing(db.get(Booking,id),'Booking')
    if u.role=='customer' and b.user_id!=u.id:raise HTTPException(403,'Not your booking')
    return b
@app.post('/bookings',response_model=BookingOut,status_code=201)
def booking_create(data:BookingIn,db:Session=Depends(db_session),u:User=Depends(current_user)):
    if availability(db,data.event_id)<data.quantity:raise HTTPException(409,'Not enough tickets')
    b=Booking(user_id=u.id,**data.model_dump());db.add(b);db.commit();db.refresh(b);return b
@app.put('/bookings/{id}',response_model=BookingOut)
def booking_update(id:int,data:BookingEdit,db:Session=Depends(db_session),u:User=Depends(current_user)):
    b=fail_if_missing(db.get(Booking,id),'Booking')
    if u.role=='customer' and b.user_id!=u.id:raise HTTPException(403,'Not your booking')
    if b.status!='confirmed':raise HTTPException(409,'Cannot modify cancelled booking')
    if data.quantity is not None:
        if availability(db,b.event_id,exclude_booking_id=id)<data.quantity:raise HTTPException(409,'Not enough tickets')
        b.quantity=data.quantity
    db.commit();db.refresh(b);return b
@app.delete('/bookings/{id}',response_model=BookingOut)
def booking_cancel(id:int,db:Session=Depends(db_session),u:User=Depends(current_user)):
    b=fail_if_missing(db.get(Booking,id),'Booking')
    if u.role=='customer' and b.user_id!=u.id:raise HTTPException(403,'Not your booking')
    b.status='cancelled';db.commit();db.refresh(b);return b
@app.get('/bookings/{id}/qr')
async def ticket_qr(id:int,db:Session=Depends(db_session),u:User=Depends(current_user)):
    """Makes a genuine HTTP request to api.qrserver.com, returning its response as URL evidence."""
    b=fail_if_missing(db.get(Booking,id),'Booking')
    if u.role=='customer' and b.user_id!=u.id:raise HTTPException(403,'Not your booking')
    if b.status!='confirmed':raise HTTPException(409,'Booking cancelled')
    payload=f'TICKET:BOOKING-{b.id}:EVENT-{b.event_id}:USER-{b.user_id}'
    url='https://api.qrserver.com/v1/create-qr-code/?size=200x200&data='+quote(payload,safe='')
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response=await client.get(url)
            response.raise_for_status()
            if not response.headers.get('content-type','').startswith('image/'):
                raise ValueError('External service returned non-image content')
    except (httpx.HTTPError,ValueError):raise HTTPException(502,'QR provider unavailable')
    return {'provider':'api.qrserver.com','request_url':url,'content_type':response.headers.get('content-type'),'image_bytes':len(response.content),'ticket_payload':payload}
