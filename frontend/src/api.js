export async function api(path, options={}) {
  const response=await fetch('/api'+path, {headers:{'Content-Type':'application/json'},...options});
  if (!response.ok) {
    const error=await response.json().catch(()=>({detail:'The local service is unavailable.'}));
    throw new Error(typeof error.detail==='string'?error.detail:'Please check the form fields.');
  }
  return response.json();
}
export const write=(path,body,method='POST')=>api(path,{method,body:JSON.stringify(body)});
export const fields=m=>Object.fromEntries(['title','summary','tags','memory_type','importance','local_only','archived','source_chat_id','source_message_ids'].filter(k=>k in m).map(k=>[k,m[k]]));
