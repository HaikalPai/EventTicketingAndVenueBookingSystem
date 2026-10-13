const api = async (route, method='GET', payload) => {
  const options={method,headers:{'Content-Type':'application/json'}};
  const token=localStorage.getItem('token'); if(token)options.headers.Authorization=`Bearer ${token}`;
  if(payload!==undefined)options.body=JSON.stringify(payload);
  const res=await fetch(route,options); const raw=await res.text(); let data;try{data=JSON.parse(raw)}catch{data=raw}
  if(!res.ok)throw Error(typeof data.detail==='string'?data.detail:JSON.stringify(data.detail||data));return data;
};
const out=(value)=>{document.querySelector('#output').textContent=JSON.stringify(value,null,2)};
async function login(){try{const data=await api('/auth/login','POST',{email:document.querySelector('#email').value,password:document.querySelector('#password').value});localStorage.setItem('token',data.access_token);out(data)}catch(e){out({error:e.message})}}
async function logout(){localStorage.removeItem('token');out({message:'Logged out'})}
async function invoke(route,method='GET',payload){try{out(await api(route,method,payload))}catch(e){out({error:e.message})}}
async function formInvoke(event,route,method){event.preventDefault();const obj=Object.fromEntries(new FormData(event.target).entries());for(const key of ['capacity','ticket_limit','venue_id','event_id','quantity'])if(obj[key]!==undefined)obj[key]=Number(obj[key]);invoke(route,method,obj)}
