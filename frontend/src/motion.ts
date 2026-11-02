"use client";
export const motionTokens = {
  duration: {none:0, instant:0.08, fast:0.18, normal:0.35, slow:0.6, crawl:1},
  easing: {smooth:[0.22,1,0.36,1] as const, sharp:[0.4,0,0.2,1] as const},
  distance: {xs:4, sm:8, md:16, lg:24},
  scale: {subtle:0.98, press:0.96, pop:1.02},
};
export const springs = {
  snappy:{type:'spring' as const,stiffness:300,damping:30},
  gentle:{type:'spring' as const,stiffness:120,damping:20},
  bouncy:{type:'spring' as const,stiffness:300,damping:24},
  instant:{type:'spring' as const,stiffness:600,damping:35},
  release:{type:'spring' as const,stiffness:200,damping:20,restDelta:0.001},
};
export function shouldAnimate(reduced:boolean, paused:boolean, essential=false) {
  if(reduced||paused)return false;
  return essential||typeof navigator==='undefined'||navigator.hardwareConcurrency>4;
}
