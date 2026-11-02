import { useEffect, useState, type FormEvent } from 'react';
import { createRoot } from 'react-dom/client';
import { languages, messages, type Language } from './i18n';
import './style.css';

type Page = 'home'|'calendar'|'create'|'inbox'|'leads'|'insights'|'store'|'settings'|'operations';
type Identity = {user: {id:string; name:string; is_staff:boolean}; workspaces:{id:string;name:string}[]};
type Item = {id:string; status?:string; action?:string; amount_paise?:number};
type Overview = {workspaces:{workspace_id:string;name:string;ai_cost_paise:number;alert:boolean}[];
  failed_jobs:{id:string;workspace_id:string;last_error:string}[];users:{id:string;name:string}[]};
const pages:Page[] = ['home','calendar','create','inbox','leads','insights','store','settings'];
const rupees = (value:number) => new Intl.NumberFormat('en-IN', {style:'currency',currency:'INR'}).format(value/100);

function App() {
  const [language,setLanguage] = useState<Language>('en');
  const [dark,setDark] = useState(false);
  const [page,setPage] = useState<Page>('home');
  const [token,setToken] = useState('');
  const [input,setInput] = useState('');
  const [identity,setIdentity] = useState<Identity|null>(null);
  const [workspace,setWorkspace] = useState('');
  const [data,setData] = useState<Record<string,Item[]>|null>(null);
  const [admin,setAdmin] = useState<Overview|null>(null);
  const [summary,setSummary] = useState<{ai_cost_paise:number;counts:Record<string,number>}|null>(null);
  const [loading,setLoading] = useState(false);
  const [error,setError] = useState(false);
  const [refresh,setRefresh] = useState(0);
  const t = messages[language];
  useEffect(() => { document.documentElement.lang=language; },[language]);
  useEffect(() => { document.documentElement.dataset.theme=dark?'dark':'light'; },[dark]);

  async function api(path:string, session=token, signal?:AbortSignal) {
    const response=await fetch(path,{headers:{Authorization:`Bearer ${session}`,'X-Workspace-ID':workspace},signal});
    if(!response.ok) throw new Error('Request failed');
    return response.json();
  }
  async function open(event:FormEvent) {
    event.preventDefault(); setLoading(true); setError(false);
    try {
      const value:Identity = await api('/v1/workspaces',input.trim());
      setToken(input.trim()); setInput(''); setIdentity(value); setWorkspace(value.workspaces[0]?.id||'');
    } catch {setError(true);} finally {setLoading(false);}
  }
  async function endSession() {
    // Revoke first; a failed revocation keeps credentials in memory to allow retry.
    setError(false);setLoading(true);
    try {
      const response=await fetch('/v1/session',{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});
      if(!response.ok && response.status!==401) throw new Error('Revocation failed');
      setToken('');setIdentity(null);setData(null);setAdmin(null);setWorkspace('');setPage('home');
    } catch {setError(true);} finally {setLoading(false);}
  }
  useEffect(() => {
    setData(null);setAdmin(null);setSummary(null);
    if(!token||!workspace) return;
    const controller=new AbortController();setLoading(true);setError(false);
    (async()=>{
      try {
        if(page==='operations') setAdmin(await api('/v1/admin/overview',token,controller.signal));
        else {
          const names=['jobs','connections','usage','audit'];
          const values=await Promise.all(names.map(name=>api(`/v1/workspaces/current/${name}`,token,controller.signal)));
          const totals=await api('/v1/workspaces/current/summary',token,controller.signal);
          if(!controller.signal.aborted) setSummary(totals);
          if(!controller.signal.aborted) setData(Object.fromEntries(names.map((name,i)=>[name,values[i].items])));
        }
      } catch {if(!controller.signal.aborted)setError(true);}
      finally {if(!controller.signal.aborted)setLoading(false);}
    })();
    return ()=>controller.abort();
  },[token,workspace,page,refresh]);

  return <div className="shell"><aside><div className="brand">s↗ <span>social growth</span></div>
    <p>{t.subtitle}</p><nav aria-label="Primary">{[...pages,...(identity?.user.is_staff?['operations' as Page]:[])].map(name=>
      <button key={name} aria-current={page===name?'page':undefined} onClick={()=>setPage(name)}>{t[name]}</button>)}</nav>
    <small>{t.notice}</small></aside><main>
    <header><div>{identity?.user.name||'Social Growth'}</div><div className="tools">
      <label>{t.language}<select aria-label={t.language} value={language} onChange={e=>setLanguage(e.target.value as Language)}>
        {languages.map(code=><option key={code} value={code}>{{en:'English',ta:'தமிழ்',hi:'हिन्दी'}[code]}</option>)}</select></label>
      <button onClick={()=>setDark(!dark)} aria-label={t.theme}>{dark?'☀':'☾'}</button></div></header>
    <section className="heading"><p>{t.subtitle}</p><h1>{t.title}</h1></section>
    {error&&<div role="alert" className="error">{t.error} <button onClick={()=>setRefresh(refresh+1)}>{t.retry}</button></div>}
    {!identity?<form className="card auth" onSubmit={open}><h2>{t.connect}</h2><p>{t.disconnected}</p>
      <label htmlFor="session">{t.token}</label><input id="session" type="password" autoComplete="off" value={input} onChange={e=>setInput(e.target.value)} required maxLength={128}/>
      <button className="primary" disabled={loading}>{loading?t.loading:t.connect}</button></form>:<>
      <div className="workspace"><label>{t.workspace}<select value={workspace} onChange={e=>setWorkspace(e.target.value)}>
        {identity.workspaces.map(row=><option key={row.id} value={row.id}>{row.name}</option>)}</select></label>
        <button disabled={loading} onClick={()=>setRefresh(refresh+1)}>{t.refresh}</button>
        <button disabled={loading} onClick={endSession}>{t.signout}</button></div>
      <div role="status" aria-live="polite">{loading?t.loading:''}</div>
      {page==='home'&&data&&<><div className="stats">{(['jobs','connections','usage','audit'] as const).map(name=><article className="card" key={name}><span>{t[name]}</span>
        <strong>{name==='usage'?rupees(summary?.ai_cost_paise||0):(summary?.counts[name]??0)}</strong></article>)}</div>
        <section className="card"><h2>{t.jobs}</h2>{data.jobs.length?data.jobs.map(row=><p key={row.id}>{row.id.slice(0,8)} · {row.status}</p>):<p>{t.noData}</p>}</section></>}
      {page==='operations'&&admin&&<section className="card"><h2>{t.operations}</h2><p>{t.staff}</p>
        <div className="stats">{admin.workspaces.map(row=><article className="card" key={row.workspace_id}><h3>{row.name}</h3><span>{t.cost}</span><strong>{rupees(row.ai_cost_paise)}</strong><p className={row.alert?'alert':''}>{row.alert?t.alert:t.healthy}</p></article>)}</div>
        <h3>{t.jobs}</h3>{admin.failed_jobs.length?admin.failed_jobs.map(row=><p key={row.id}>{row.id.slice(0,8)} · {row.last_error}</p>):<p>{t.noData}</p>}</section>}
      {page!=='home'&&page!=='operations'&&<section className="card"><span className="pill">{t.planned}</span><h2>{t[page]}</h2><p>{t.empty}</p></section>}
    </>}
    <footer>{t.notice}</footer>
  </main></div>;
}

createRoot(document.getElementById('root')!).render(<App/>);
