export async function api(path, options={}) {
  const response=await fetch('/api'+path, {headers:{'Content-Type':'application/json'},...options});
  if (!response.ok) {
    const error=await response.json().catch(()=>({detail:'The local service is unavailable.'}));
    throw new Error(typeof error.detail==='string'?error.detail:'Please check the form fields.');
  }
  return response.json();
}
export const write=(path,body,method='POST')=>api(path,{method,body:JSON.stringify(body)});
export async function streamChat(body, onAnswer) {
  const response=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
  if(!response.ok) throw new Error('The chat service is unavailable.');
  const reader=response.body.getReader(),decoder=new TextDecoder();
  let buffer='',result;
  const receive=line=>{
    if(!line.trim()) return;
    const event=JSON.parse(line);
    if(event.type==='error') throw new Error(event.detail);
    if(event.type==='answer') onAnswer(event.result);
    if(event.type==='complete') result=event.result;
  };
  try {
    while(true){const {value,done}=await reader.read();buffer+=decoder.decode(value,{stream:!done});const lines=buffer.split('\n');buffer=lines.pop();lines.forEach(receive);if(done)break;}
    if(buffer.trim())receive(buffer);
    if(!result)throw new Error('The connection ended before the reply was saved.');
    return result;
  } finally {reader.releaseLock();}
}
export const fields=m=>Object.fromEntries(['title','summary','tags','memory_type','importance','local_only','archived','source_chat_id','source_message_ids'].filter(k=>k in m).map(k=>[k,m[k]]));
