import {useEffect,useRef,useState} from 'react';
import {Button,Icon} from './ui';

type Row=Record<string,string|number|boolean|null>;
const collections={'api-errors':'API errors','cost-alerts':'Cost alerts','users':'Users','workspaces':'Workspaces','failed-jobs':'Failed jobs'};
const columns:Record<string,string[]>={
 'api-errors':['route','status','code','request_id'],
 'cost-alerts':['workspace_id','period','status','attempts'],
 users:['name','is_staff','id'],workspaces:['name','ai_cost_paise','alert'],
 'failed-jobs':['id','last_error','attempts'],
};
export function OperationsRecords({api}:{api:(path:string)=>Promise<{items:Row[];next_cursor:string|null}>}){
 const [tab,setTab]=useState<keyof typeof collections>('api-errors');
 const [rows,setRows]=useState<Row[]>([]),[cursor,setCursor]=useState<string|null>(null);
 const [loading,setLoading]=useState(false),[error,setError]=useState(false),[reload,setReload]=useState(0);
 const fetcher=useRef(api);fetcher.current=api;
 useEffect(()=>{
  let active=true;setLoading(true);setError(false);setRows([]);setCursor(null);
  fetcher.current(`/v1/admin/${tab}?limit=25`).then(value=>{
   if(active){setRows(value.items);setCursor(value.next_cursor);}
  }).catch(()=>{if(active)setError(true);}).finally(()=>{if(active)setLoading(false);});
  return()=>{active=false;};
 },[tab,reload]);
 async function more(){
  if(!cursor||loading)return;setLoading(true);setError(false);
  try{const value=await fetcher.current(`/v1/admin/${tab}?limit=25&after=${encodeURIComponent(cursor)}`);
   setRows(previous=>[...previous,...value.items]);setCursor(value.next_cursor);
  }catch{setError(true);}finally{setLoading(false);}
 }
 return <section className="surface operations-records"><div className="panel-title"><h2>Operational records</h2><Icon name="operations"/></div>
  <div className="filter-tabs" aria-label="Operational record type">{Object.entries(collections).map(([key,label])=><Button key={key} disabled={loading} aria-pressed={tab===key} onClick={()=>setTab(key as keyof typeof collections)}>{label}</Button>)}</div>
  {error&&<p role="alert">Records could not be loaded. <Button className="text-button" onClick={()=>setReload(reload+1)}>Retry records</Button></p>}
  {loading&&<p role="status">Loading records…</p>}
  {rows.length>0?<div className="records-scroll"><table><thead><tr>{columns[tab].map(column=><th key={column}>{column.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={String(row.id||row.workspace_id||index)}>{columns[tab].map(column=><td key={column}>{typeof row[column]==='boolean'?(row[column]?'Yes':'No'):String(row[column]??'—')}</td>)}</tr>)}</tbody></table></div>:!loading&&!error&&<p>No records yet.</p>}
  {cursor&&<Button className="secondary" disabled={loading} onClick={more}>Load more records<Icon name="arrow"/></Button>}
 </section>;
}
