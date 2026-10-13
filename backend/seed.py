"""Populate safe fictional demo records. Run: python -m backend.seed"""
from datetime import datetime,timedelta,timezone
from sqlalchemy import select
from backend.main import SessionLocal,User,Venue,Event,Booking,password_hash
with SessionLocal() as db:
    accounts=[('Project Admin','admin@demo.example.com','admin'),('Event Organiser','organiser@demo.example.com','organiser'),('Venue Staff','staff@demo.example.com','staff'),('Customer One','customer1@demo.example.com','customer'),('Customer Two','customer2@demo.example.com','customer')]
    for name,email,role in accounts:
        if not db.scalar(select(User).where(User.email==email)):db.add(User(name=name,email=email,role=role,password_hash=password_hash.hash('DemoPass123!')))
    db.commit()
    venues=[('Grand Hall','Kuala Lumpur',500),('Sky Auditorium','Shah Alam',200),('Open Garden','Putrajaya',300),('Creative Studio','Petaling Jaya',80),('City Arena','Cyberjaya',1000)]
    for name,location,capacity in venues:
        if not db.scalar(select(Venue).where(Venue.name==name)):db.add(Venue(name=name,location=location,capacity=capacity))
    db.commit()
    organiser=db.scalar(select(User).where(User.email=='organiser@demo.example.com'))
    for idx,name in enumerate(['Tech Futures Expo','Community Music Night','Startup Pitch Day','Digital Art Workshop','University Career Fair']):
        if not db.scalar(select(Event).where(Event.name==name)):
            venue=db.scalar(select(Venue).where(Venue.name==venues[idx][0]))
            db.add(Event(name=name,description='Fictional demonstration event',venue_id=venue.id,organiser_id=organiser.id,starts_at=(datetime.now(timezone.utc)+timedelta(days=20+idx)).replace(tzinfo=None),ticket_limit=min(venue.capacity,50+idx*25)))
    db.commit()
    customer=db.scalar(select(User).where(User.email=='customer1@demo.example.com'))
    for ev in list(db.scalars(select(Event).order_by(Event.id).limit(5))):
        if not db.scalar(select(Booking).where(Booking.event_id==ev.id,Booking.user_id==customer.id)):db.add(Booking(event_id=ev.id,user_id=customer.id,quantity=2,status='confirmed'))
    db.commit()
print('Seed complete: >=5 records in each of the four core tables. Demo password DemoPass123!')
