"use client";
import {createContext, useContext, type ComponentProps, type ReactNode, useRef, useEffect} from 'react';
import {motion, useInView, useMotionValue, useSpring} from 'motion/react';
import {motionTokens, shouldAnimate, springs} from './motion';

export const AnimationContext=createContext(true);
export function Button(props:ComponentProps<typeof motion.button>) {
  const animate=useContext(AnimationContext);
  return <motion.button {...props} whileHover={animate&&!props.disabled?{y:-motionTokens.distance.xs/2}:undefined}
    whileTap={animate&&!props.disabled?{scale:motionTokens.scale.press}:undefined} transition={springs.snappy}/>;
}
const paths:Record<string,ReactNode>={
  home:<><path d="m3 10 9-7 9 7v10H3Z"/><path d="M9 20v-7h6v7"/></>,
  calendar:<><rect x="3" y="5" width="18" height="16" rx="3"/><path d="M7 3v4m10-4v4M3 11h18m-12 4h2m4 0h2"/></>,
  create:<><rect x="3" y="3" width="18" height="18" rx="5"/><path d="M12 7v10m-5-5h10"/></>,
  inbox:<><path d="M4 4h16v15H4Z"/><path d="M4 13h5l1 3h4l1-3h5"/></>,
  leads:<><circle cx="9" cy="8" r="3"/><path d="M3 20v-3a6 6 0 0 1 12 0v3m2-15a3 3 0 0 1 0 6m1 3a5 5 0 0 1 3 5"/></>,
  insights:<><path d="M4 20V4m0 16h17M8 15l4-4 4 2 5-8"/></>,
  store:<><path d="M4 9h16l-2-5H6Zm1 0v12h14V9M9 21v-7h6v7"/></>,
  settings:<><path d="M4 7h16M4 17h16"/><circle cx="9" cy="7" r="3"/><circle cx="16" cy="17" r="3"/></>,
  operations:<><path d="m12 3 9 4v5c0 5-9 9-9 9s-9-4-9-9V7Z"/><path d="m8 12 3 3 5-6"/></>,
  arrow:<path d="M5 12h14m-5-5 5 5-5 5"/>,
  diagonal:<path d="M6 18 18 6M6 6h12v12"/>,
  search:<><circle cx="10" cy="10" r="6"/><path d="m15 15 5 5"/></>,
  check:<path d="m5 12 4 4L19 6"/>,
  lock:<><rect x="5" y="10" width="14" height="11" rx="3"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/></>,
  spark:<><path d="m12 3 2.5 6.5L21 12l-6.5 2.5L12 21l-2.5-6.5L3 12l6.5-2.5Z"/></>,
  sun:<><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1 1m12 12 1 1M5 19l1-1M18 6l1-1"/></>,
  moon:<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>,
  pause:<><path d="M8 5v14m8-14v14"/></>,
  play:<path d="m8 4 12 8-12 8Z"/>,
  close:<path d="m6 6 12 12M6 18 18 6"/>,
  refresh:<><path d="M20 8a8 8 0 1 0 0 8M20 3v6h-6"/></>,
  exit:<><path d="M10 3H4v18h6m4-14 5 5-5 5m-6-5h11"/></>,
  roadmap:<><circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M5 7v6h14V7H9m10 6v4"/></>,
  folder:<path d="M3 7V4h7l3 3h8v13H3Z"/>,
};
export function Icon({name,className=''}:{name:string;className?:string}) {
  return <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]||paths.spark}</svg>;
}
export function Mascot({onClick,compact=false,label}:{onClick:()=>void;compact?:boolean;label:string}) {
  const motionEnabled=useContext(AnimationContext);
  const scene=useRef<HTMLDivElement>(null);
  const visible=useInView(scene,{margin:'50px'});
  const enabled=motionEnabled&&shouldAnimate(false,false)&&visible;
  const rx=useMotionValue(0),ry=useMotionValue(0);
  const rotateX=useSpring(rx,springs.gentle),rotateY=useSpring(ry,springs.gentle);
  useEffect(()=>{if(!enabled){rx.set(0);ry.set(0);}},[enabled,rx,ry]);
  return <div ref={scene} className={`mascot-scene ${compact?'compact':''}`} onPointerMove={e=>{
    if(!enabled||e.pointerType==='touch')return;
    const rect=e.currentTarget.getBoundingClientRect();
    ry.set(((e.clientX-rect.left)/rect.width-.5)*motionTokens.distance.lg);
    rx.set(-((e.clientY-rect.top)/rect.height-.5)*motionTokens.distance.md);
  }} onPointerLeave={()=>{rx.set(0);ry.set(0);}}>
    <div className="scene-grid"/><div className="planet-ring ring-one"/><div className="planet-ring ring-two"/>
    <motion.span className="floating-cube" initial={false} animate={enabled?{y:[0,-motionTokens.distance.sm,0],rotate:[-12,-4,-12]}:{y:0,rotate:0}}
      transition={{duration:enabled?motionTokens.duration.crawl*5:motionTokens.duration.none,repeat:enabled?Infinity:0,ease:'easeInOut'}}><Icon name="spark"/></motion.span>
    <motion.div className="mascot-tilt" style={{rotateX:enabled?rotateX:0,rotateY:enabled?rotateY:0}}>
      <motion.div initial={false} animate={enabled?{y:[0,-motionTokens.distance.sm,0]}:{y:0}}
        transition={{duration:enabled?motionTokens.duration.crawl*4:motionTokens.duration.none,repeat:enabled?Infinity:0,ease:'easeInOut'}}>
        <Button type="button" className="mascot" onClick={onClick} aria-label={label}>
          <span className="antenna"><span/></span><span className="pip-ear left"/><span className="pip-ear right"/>
          <span className="pip-head"><span className="pip-highlight"/><span className="pip-face"><span className="pip-eye"/><span className="pip-eye"/><span className="pip-smile"/></span><span className="pip-cheek"/></span>
          <span className="pip-body"><span className="pip-badge">✳</span></span><span className="pip-arm left"/><span className="pip-arm right"/><span className="pip-foot left"/><span className="pip-foot right"/>
        </Button>
      </motion.div>
    </motion.div>
    <span className="mascot-shadow"/><span className="scene-spark spark-one">✦</span><span className="scene-spark spark-two">✦</span>
    <span className="scene-chip"><span/> APPROVAL FIRST</span>
  </div>;
}
export function Dialog({title,children,onClose}:{title:string;children:ReactNode;onClose:()=>void}) {
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null;
    ref.current?.showModal();
    return ()=>{ref.current?.close();previous?.focus();};
  },[]);
  return <dialog ref={ref} className="guide-dialog" onCancel={e=>{e.preventDefault();onClose();}} onClick={e=>{if(e.target===e.currentTarget)onClose();}}>
    <div className="dialog-heading"><div><span className="eyebrow">YOUR GROWTH COMPANION</span><h2>{title}</h2></div><Button className="icon-button" aria-label="Close guide" onClick={onClose}><Icon name="close"/></Button></div>{children}
  </dialog>;
}
