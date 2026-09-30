import React, {useMemo} from 'react';
import {SpatialScene} from './Constellation';

export default function MemoryMap({selected, memories, onSelect}) {
  const nodes=useMemo(()=>{
    const tags=new Set((selected.tags||[]).map(tag=>tag.toLowerCase()));
    const related=memories.filter(memory=>memory.memory_id!==selected.memory_id&&!memory.archived&&(memory.tags||[]).some(tag=>tags.has(tag.toLowerCase()))).slice(0,8);
    return [{id:selected.memory_id,label:selected.title,level:0,position:[0,0,0],size:9,color:'#cfbdfb',memory:selected},...related.map((memory,index)=>({id:memory.memory_id,parentId:selected.memory_id,label:memory.title,level:1,position:[Math.cos(index*2.4)*24,Math.sin(index*2.4)*17,Math.sin(index*1.7)*14],size:4.2,color:'#bda7f5',memory}))];
  },[selected,memories]);
  return <section className="memory-detail-map"><strong>Memory connections</strong><p className="muted">Connections represent shared tags.</p><SpatialScene nodes={nodes} onSelect={node=>{if(node?.memory&&node.id!==selected.memory_id)onSelect(node.memory);}}/></section>;
}
