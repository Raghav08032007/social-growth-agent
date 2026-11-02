"use client";
import {useEffect, useState, type FormEvent} from 'react';
import {createRoot} from 'react-dom/client';
import {AnimatePresence, MotionConfig, motion, useReducedMotion} from 'motion/react';
import {languages, messages, type Language} from './i18n';
import {experience, phaseNames, phaseCounts} from './experience';
import {AnimationContext, Button, Dialog, Icon, Mascot} from './ui';
import {motionTokens, shouldAnimate, springs} from './motion';
import {OperationsRecords} from './operations';
import './style.css';

type Page='home'|'calendar'|'create'|'inbox'|'leads'|'insights'|'store'|'settings'|'operations'|'roadmap';
type Identity={user:{id:string;name:string;is_staff:boolean};workspaces:{id:string;name:string}[]};
type Item={id:string;status?:string;action?:string;amount_paise?:number;created_at?:number};
type Overview={workspaces:{workspace_id:string;name:string;ai_cost_paise:number;alert:boolean}[];failed_jobs:{id:string;workspace_id:string;last_error:string}[];users:{id:string;name:string}[]};
const pages:Page[]=['home','calendar','create','inbox','leads','insights','store','settings'];
const rupees=(value:number)=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR'}).format(value/100);
const modulePhases:Record<string,number>={calendar:1,create:1,inbox:2,leads:2,insights:3,store:3,settings:0};

function App(){
 const [language,setLanguage]=useState<Language>('en');
 const [dark,setDark]=useState(false),[paused,setPaused]=useState(false);
 const [page,setPage]=useState<Page>('home');
 const [token,setToken]=useState(''),[input,setInput]=useState('');
 const [identity,setIdentity]=useState<Identity|null>(null),[workspace,setWorkspace]=useState('');
 const [data,setData]=useState<Record<string,Item[]>|null>(null),[admin,setAdmin]=useState<Overview|null>(null);
 const [summary,setSummary]=useState<{ai_cost_paise:number;counts:Record<string,number>}|null>(null);
 const [loading,setLoading]=useState(false),[error,setError]=useState(false),[refresh,setRefresh]=useState(0);
 const [preview,setPreview]=useState(false),[guide,setGuide]=useState(false),[query,setQuery]=useState('');
 const [missing,setMissing]=useState<string[]>([]),[jobFilter,setJobFilter]=useState('all');
 const [online,setOnline]=useState(()=>navigator.onLine);
 const initialReduced=useReducedMotion()===true;
 const [reduced,setReduced]=useState(initialReduced);
 const feedback=shouldAnimate(reduced,paused,true);
 const t=messages[language],x=experience[language];
 const title=(name:Page)=>name==='roadmap'?x.roadmap:t[name];
 const allPages:Page[]=[...pages,'roadmap',...(identity?.user.is_staff?['operations' as Page]:[])];
 const navigate=(name:Page)=>{setPage(name);setQuery('');window.scrollTo({top:0,behavior:'instant'});};
 useEffect(()=>{
  const update=()=>setOnline(navigator.onLine);
  window.addEventListener('online',update);window.addEventListener('offline',update);
  if(import.meta.env.PROD&&'serviceWorker' in navigator){
   navigator.serviceWorker.register('/sw.js').catch(()=>{/* Network-only mode remains usable. */});
  }
  return()=>{window.removeEventListener('online',update);window.removeEventListener('offline',update);};
 },[]);
 useEffect(()=>{
  const preference=window.matchMedia('(prefers-reduced-motion: reduce)');
  const update=()=>setReduced(preference.matches);
  update();preference.addEventListener('change',update);
  return()=>preference.removeEventListener('change',update);
 },[]);
 useEffect(()=>{document.documentElement.lang=language;},[language]);
 useEffect(()=>{document.documentElement.dataset.theme=dark?'dark':'light';},[dark]);
 useEffect(()=>{document.documentElement.dataset.motion=feedback?'on':'off';},[feedback]);
 async function api(path:string,session=token,signal?:AbortSignal){
  const response=await fetch(path,{headers:{Authorization:`Bearer ${session}`,'X-Workspace-ID':workspace},signal});
  if(!response.ok)throw new Error('Request failed');
  return response.json();
 }
 async function open(event:FormEvent){
  event.preventDefault();setLoading(true);setError(false);
  try{
   const value:Identity=await api('/v1/workspaces',input.trim());
   setToken(input.trim());setInput('');setIdentity(value);setPreview(false);setPage('home');
   setWorkspace(value.workspaces[0]?.id||'');
   window.scrollTo({top:0,behavior:'instant'});
  }catch{setError(true);}finally{setLoading(false);}
 }
 async function endSession(){
  setError(false);setLoading(true);
  try{
   const response=await fetch('/v1/session',{method:'DELETE',headers:{Authorization:`Bearer ${token}`}});
   if(!response.ok&&response.status!==401)throw new Error('Revocation failed');
   setToken('');setIdentity(null);setData(null);setAdmin(null);setWorkspace('');setPage('home');
   window.scrollTo({top:0,behavior:'instant'});
  }catch{setError(true);}finally{setLoading(false);}
 }
 useEffect(()=>{
  setData(null);setAdmin(null);setSummary(null);setMissing([]);
  if(!token||!workspace)return;
  const controller=new AbortController();setLoading(true);setError(false);
  (async()=>{
   try{
    if(page==='operations'){
     const result=await api('/v1/admin/overview',token,controller.signal);
     if(!controller.signal.aborted)setAdmin(result);
    }else{
     const names=['jobs','connections','usage','audit','summary'];
     const results=await Promise.allSettled(names.map(name=>api(`/v1/workspaces/current/${name}`,token,controller.signal)));
     if(controller.signal.aborted)return;
     const available:Record<string,Item[]>={},unavailable:string[]=[];
     results.forEach((result,index)=>{
      if(result.status==='rejected')unavailable.push(names[index]);
      else if(names[index]==='summary')setSummary(result.value);
      else available[names[index]]=result.value.items;
     });
     setData(Object.keys(available).length?available:null);setMissing(unavailable);
     if(unavailable.length===names.length)setError(true);
    }
   }catch{if(!controller.signal.aborted)setError(true);}
   finally{if(!controller.signal.aborted)setLoading(false);}
  })();
  return()=>controller.abort();
 },[token,workspace,page,refresh]);

 function roadmap(){return <>
  <div className="section-heading"><div><span className="eyebrow">BUILDING WITH INTENTION</span><h1>{x.roadmap}</h1><p>{x.roadmapBody}</p></div><span className="date-tag">02 NOV 2026</span></div>
  <div className="progress-metrics">{[[x.phases,'0 / 11'],[x.completed,'0 / 257'],[x.inProgress,'4'],[x.notStarted,'253']].map(([label,value])=><div key={label}><strong>{value}</strong><span>{label}</span></div>)}</div>
  <div className="phase-list">{phaseNames.map((name,i)=><article key={name} className={`phase-row ${i===0?'current':''}`}><span className="phase-number">{String(i).padStart(2,'0')}</span><div><h3>{name}</h3><p>{phaseCounts[i]} features</p></div><span className="phase-state">{i===0?x.inProgress:x.notStarted}</span><Icon name={i===0?'spark':'lock'}/></article>)}</div>
 </>;}
 function checklist(){return <section className="surface checklist"><div className="panel-title"><div><span className="eyebrow">ONE STEP AT A TIME</span><h2>{x.setup}</h2></div><Icon name="roadmap"/></div><p className="muted">{x.setupBody}</p>{[
  [x.stepOne,x.stepOneBody,!!identity],[x.stepTwo,x.stepTwoBody,false],[x.stepThree,x.stepThreeBody,false]
 ].map(([label,body,done],i)=><Button className="checklist-row" key={i} onClick={()=>{if(i===0&&!identity){setPreview(false);navigate('home');}else navigate(i===1?'home':'roadmap');}}><span className={`step-dot ${done?'done':''}`}>{done?<Icon name="check"/>:String(i+1).padStart(2,'0')}</span><span><strong>{label}</strong><small>{body}</small></span><Icon name="diagonal"/></Button>)}</section>;}
 function home(){
  const jobs=data?.jobs||[],filtered=jobFilter==='all'?jobs:jobs.filter(row=>row.status===jobFilter);
  return <>
   <div className="section-heading"><div><span className="eyebrow">{x.today}</span><h1>{identity?`${t.home}, ${identity.user.name.split(' ')[0]}.`:x.previewTitle}</h1><p>{identity?x.greeting:x.previewSub}</p></div><Button className="primary" onClick={()=>navigate('roadmap')}>{x.seePlan}<Icon name="arrow"/></Button></div>
   <section className="growth-hero"><div className="hero-copy"><span className="tag"><Icon name="spark"/>{x.next}</span><h2>{x.phaseZero}</h2><p>{x.phaseZeroBody}</p><Button className="hero-link" onClick={()=>setGuide(true)}>{x.meet}<Icon name="arrow"/></Button><div className="hero-footnote"><span className="small-avatars"><i>R</i><i>P</i></span><span>YOU + PIP <b>·</b> BUILT AROUND YOUR APPROVAL</span></div></div><Mascot onClick={()=>setGuide(true)} label={x.meet}/></section>
   {preview?<DesignPreview x={x}/>:<>
    <div className="stats">{(['jobs','connections','usage','audit'] as const).map((name,i)=><motion.article className="metric" key={name} initial={false} whileHover={feedback?{y:-motionTokens.distance.xs}:undefined} transition={springs.gentle}><div className="metric-top"><span>{t[name]}</span><span className={`metric-icon color-${i}`}><Icon name={['folder','leads','insights','operations'][i]}/></span></div><strong>{missing.includes(name)||!summary?'—':name==='usage'?rupees(summary.ai_cost_paise):(summary.counts[name]??0)}</strong><small>{name==='usage'?t.cost:x.overview}</small></motion.article>)}</div>
    <div className="dashboard-columns"><section className="surface activity"><div className="panel-title"><div><span className="eyebrow">BEHIND THE SCENES</span><h2>{t.jobs}</h2></div><Icon name="folder"/></div><div className="filter-tabs" aria-label="Job filter">{['all','succeeded','dead_letter'].map(filter=><Button key={filter} aria-pressed={jobFilter===filter} onClick={()=>setJobFilter(filter)}>{filter==='all'?'All':filter==='succeeded'?'Succeeded':'Needs attention'}</Button>)}</div>
     {missing.includes('jobs')?<div className="empty-state"><Icon name="operations"/><p>{t.error}</p><Button className="text-button" onClick={()=>setRefresh(refresh+1)}>{t.retry}<Icon name="refresh"/></Button></div>:filtered.length?<div className="job-list">{filtered.map(row=><div key={row.id} className="job-row"><span className={`job-dot ${row.status==='succeeded'?'success':''}`}><Icon name={row.status==='succeeded'?'check':'folder'}/></span><span><strong>Job #{row.id.slice(0,8)}</strong><small>{row.status}</small></span><span className="status-tag">{row.status}</span></div>)}</div>:<div className="empty-state"><span className="empty-icon"><Icon name="folder"/></span><h3>{x.nothing}</h3><p>{x.nothingBody}</p><Button className="text-button" onClick={()=>navigate('roadmap')}>{x.seePlan}<Icon name="arrow"/></Button></div>}
    </section>{checklist()}</div>
   </>}
  </>;
 }
 function planned(){return <><div className="section-heading"><div><span className="eyebrow">YOUR WORKSPACE</span><h1>{title(page)}</h1><p>{x.moduleBody}</p></div><span className="tag">{t.planned} · Phase {modulePhases[page]??1}</span></div><div className="planned-grid"><section className="surface planned-panel"><span className="large-icon"><Icon name={page}/></span><h2>{title(page)}</h2><p>{t.empty}</p><div className="workflow-steps">{[x.stepOne,x.stepTwo,x.stepThree].map((label,i)=><div key={label}><span>{i+1}</span>{label}<Icon name={i===0?'check':'lock'}/></div>)}</div><Button className="primary" onClick={()=>navigate('roadmap')}>{x.seePlan}<Icon name="arrow"/></Button></section>{checklist()}</div></>;}

 return <MotionConfig reducedMotion={reduced||paused?'always':'user'}><AnimationContext.Provider value={feedback}>
 <a className="skip-link" href="#main">Skip to content</a><div className="shell">
  <aside className="sidebar"><Button className="brand" onClick={()=>navigate('home')} aria-label="Social Growth home"><span className="brand-symbol">s<span>↗</span></span><span>social growth<small>ROOM TO GROW.</small></span></Button>
   <div className="workspace-identity"><span className="workspace-avatar">{identity?.user.name[0]||'s'}</span><div><strong>{identity?.workspaces.find(row=>row.id===workspace)?.name||'Your workspace'}</strong><small>{preview?x.previewLabel:identity?x.overview:'Social Growth Agent'}</small></div><Icon name="settings"/></div>
   <span className="nav-section">WORKSPACE</span><nav aria-label={x.nav}>{[...pages,...(identity?.user.is_staff?['operations' as Page]:[])].map(name=><Button key={name} className="nav-item" aria-label={title(name)} title={title(name)} aria-current={page===name?'page':undefined} onClick={()=>navigate(name)}><Icon name={name}/><span>{title(name)}</span>{['calendar','create','inbox','leads','insights','store'].includes(name)&&<span className="nav-dot"/>}</Button>)}</nav>
   <div className="sidebar-bottom"><Button className={`nav-item ${page==='roadmap'?'selected':''}`} onClick={()=>navigate('roadmap')}><Icon name="roadmap"/><span>{x.roadmap}</span><span className="nav-count">11</span></Button><div className="pip-note"><span className="mini-pip">✳</span><h3>A little help.<br/>A lot of possibility.</h3><Button onClick={()=>setGuide(true)}>{x.meet}<Icon name="diagonal"/></Button></div><div className="sidebar-profile"><span className="profile-avatar">{identity?.user.name[0]||'G'}</span><div><strong>{identity?.user.name||'Guest explorer'}</strong><small>{identity?x.overview:x.previewLabel}</small></div></div></div>
  </aside>
  <div className="app-main"><header className="topbar"><div className="breadcrumb">{t.workspace}<span>/</span><strong>{title(page)}</strong></div><div className="topbar-tools"><div className="search-wrap"><Icon name="search"/><input aria-label={x.search} placeholder={x.search} value={query} onChange={e=>setQuery(e.target.value)} onKeyDown={e=>{if(e.key==='Escape')setQuery('');}}/>{query&&<div className="search-results">{allPages.filter(name=>title(name).toLowerCase().includes(query.toLowerCase())).map(name=><Button key={name} onClick={()=>navigate(name)}><Icon name={name}/>{title(name)}<Icon name="arrow"/></Button>)}{!allPages.some(name=>title(name).toLowerCase().includes(query.toLowerCase()))&&<p>{x.noMatches}</p>}</div>}</div><select className="language-select" aria-label={t.language} value={language} onChange={e=>setLanguage(e.target.value as Language)}>{languages.map(code=><option key={code} value={code}>{{en:'EN',ta:'தமிழ்',hi:'हिन्दी'}[code]}</option>)}</select><Button className="icon-button motion-toggle" aria-label={paused?x.resume:x.pause} aria-pressed={paused} onClick={()=>setPaused(!paused)}><Icon name={paused?'play':'pause'}/></Button><Button className="icon-button" aria-label={t.theme} onClick={()=>setDark(!dark)}><Icon name={dark?'sun':'moon'}/></Button><span className="header-avatar">{identity?.user.name[0]||'G'}</span></div></header>
  <main id="main" tabIndex={-1}>
   {!online&&<div className="partial-notice" role="status">You’re offline. The public shell and design preview remain available. Workspace data and actions require a connection.</div>}
   {preview&&<div className="preview-banner"><span><Icon name="spark"/><strong>{x.previewLabel}</strong> {x.previewBody}</span><Button onClick={()=>{setPreview(false);navigate('home');}}>{x.exitPreview}<Icon name="arrow"/></Button></div>}
   {identity&&<div className="workspace-toolbar"><label>{t.workspace}<select value={workspace} onChange={e=>setWorkspace(e.target.value)}>{identity.workspaces.map(row=><option key={row.id} value={row.id}>{row.name}</option>)}</select></label><span className="toolbar-spacer"/><Button className="quiet-button" disabled={loading} onClick={()=>setRefresh(refresh+1)}><Icon name="refresh"/>{t.refresh}</Button><Button className="quiet-button" disabled={loading} onClick={endSession}><Icon name="exit"/>{t.signout}</Button></div>}
   {error&&<div role="alert" className="error"><Icon name="operations"/><span>{t.error}</span><Button onClick={()=>setRefresh(refresh+1)}>{t.retry}</Button></div>}
   {missing.length>0&&!error&&<div className="partial-notice" role="status">Some sections are unavailable: {missing.join(', ')}. <Button onClick={()=>setRefresh(refresh+1)}>{t.retry}</Button></div>}
   <AnimatePresence mode="wait" initial={false}><motion.div key={`${page}-${identity?'member':preview?'preview':'guest'}`} initial={{opacity:1}} animate={{opacity:1}} exit={{opacity:0}} transition={{duration:motionTokens.duration.fast}} className="page-content">
    {page==='roadmap'?roadmap():!identity&&!preview?<section className="welcome-layout"><div className="welcome-art"><span className="eyebrow">MAKE YOUR NEXT MOVE</span><h1>{x.welcome}</h1><p>{x.welcomeBody}</p><Mascot onClick={()=>setGuide(true)} label={x.meet}/><div className="welcome-caption"><Icon name="operations"/><span>YOUR IDEAS. YOUR APPROVAL. YOUR GROWTH.</span></div></div><div className="welcome-form-wrap"><form className="auth surface" onSubmit={open}><span className="auth-icon"><Icon name="lock"/></span><span className="eyebrow">A SPACE FOR YOUR BUSINESS</span><h2>{t.connect}</h2><p>{t.disconnected}</p><label htmlFor="session">{t.token}</label><div className="token-input"><Icon name="lock"/><input id="session" type="password" autoComplete="off" placeholder="••••••••••••••••••••" value={input} onChange={e=>setInput(e.target.value)} required maxLength={128}/></div><Button className="primary full" disabled={loading}>{loading?t.loading:t.connect}<Icon name="arrow"/></Button><div className="form-divider"><span>OR TAKE A LOOK AROUND</span></div><Button type="button" className="secondary full" onClick={()=>{setError(false);setPreview(true);navigate('home');}}>{x.preview}<Icon name="diagonal"/></Button><details className="session-help"><summary>{x.sessionHelp}</summary><p>{x.sessionHelpBody}</p><a href="https://github.com/Raghav08032007/social-growth-agent/blob/main/docs/foundation-setup.md" target="_blank" rel="noreferrer">{x.viewSetup}<Icon name="diagonal"/></a></details></form><p className="form-footnote"><Icon name="operations"/> {t.notice}</p></div></section>:<>
     {loading?<div className="loading-state" role="status"><span className="loading-mark">✳</span>{t.loading}<div className="skeleton-grid"><div/><div/><div/></div></div>:page==='home'?home():page==='operations'?admin?<section className="operations-page"><div className="section-heading"><div><span className="eyebrow">WORKSPACE HEALTH</span><h1>{t.operations}</h1><p>{t.staff}</p></div><span className="tag"><Icon name="lock"/>STAFF</span></div><div className="stats">{admin.workspaces.map(row=><article className="metric" key={row.workspace_id}><span>{row.name}</span><strong>{rupees(row.ai_cost_paise)}</strong><small>{t.cost}</small><p className={row.alert?'cost-alert':'cost-healthy'}><Icon name={row.alert?'operations':'check'}/>{row.alert?t.alert:t.healthy}</p></article>)}</div><section className="surface"><h2>{t.jobs}</h2>{admin.failed_jobs.length?admin.failed_jobs.map(row=><p className="job-row" key={row.id}><Icon name="folder"/>{row.id.slice(0,8)} · {row.last_error}</p>):<p>{t.noData}</p>}</section><OperationsRecords api={api}/></section>:<div className="surface empty-state"><Icon name="lock"/><h2>{t.staff}</h2><Button onClick={()=>navigate('home')}>{x.returnHome}</Button></div>:planned()}
    </>}
   </motion.div></AnimatePresence>
   <footer><span>social growth <b>✳</b> <span>SMALL STEPS. BIGGER POSSIBILITIES.</span></span><Button className="text-button" onClick={()=>setGuide(true)}>{x.meet}<Icon name="diagonal"/></Button></footer>
  </main></div>
 </div>{guide&&<Dialog title={x.guide} onClose={()=>setGuide(false)}><div className="guide-intro"><div className="guide-mark">✳</div><p>{x.guideBody}</p></div><div className="guide-actions"><Button onClick={()=>{setGuide(false);navigate('roadmap');}}><Icon name="roadmap"/><span>{x.seePlan}</span><Icon name="arrow"/></Button><Button onClick={()=>{setGuide(false);setError(false);if(!identity)setPreview(true);navigate('home');}}><Icon name="home"/><span>{identity?x.returnHome:x.preview}</span><Icon name="arrow"/></Button></div></Dialog>}
 </AnimationContext.Provider></MotionConfig>;
}

function DesignPreview({x}:{x:typeof experience.en}){
 return <div className="design-preview-content"><div className="preview-section-label"><span className="eyebrow">{x.sample.toUpperCase()} / PRODUCT DIRECTION</span><span className="sample-badge">{x.previewLabel}</span></div><div className="preview-grid"><section className="surface content-preview"><div className="panel-title"><h2>{x.studio}</h2><span className="sample-badge">{x.postDraft}</span></div><div className="sample-post"><div className="poster-art"><span>LUNA STUDIO</span><strong>Good hair.<br/><i>Better days.</i></strong><div className="poster-arch"/><span className="poster-star">✳</span><small>A LITTLE TIME, JUST FOR YOU.</small></div><div className="sample-post-copy"><span className="platform-label">◎ INSTAGRAM · {x.sample}</span><h3>{x.samplePost}</h3><p>{x.sampleCaption}</p><span className="sample-badge">{x.postDraft}</span></div></div></section><section className="surface pipeline-preview"><span className="eyebrow">THE BIGGER PICTURE</span><h2>{x.path}</h2><p>{x.pathBody}</p><div className="pipeline-art" aria-hidden="true"><span><Icon name="create"/></span><i/><span><Icon name="check"/></span><i/><span><Icon name="insights"/></span></div><div className="preview-disclaimer"><Icon name="lock"/>{x.previewBody}</div></section></div></div>;
}
createRoot(document.getElementById('root')!).render(<App/>);
