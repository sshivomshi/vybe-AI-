import React from 'react';

// Decorative, CSS-only scene. Motion follows the system accessibility preference.
export default function SpaceScene({background=false}) {
  return <div className={'space-scene'+(background?' planet-background':'')} aria-hidden="true">
    <div className="space-stars">{Array.from({length: 32}, (_, i) => <i key={i} style={{left: `${(i * 37 + 11) % 100}%`, top: `${(i * 23 + 7) % 100}%`, animationDelay: `${i * -.31}s`}}/>)}</div>
    {background ? <><div className="planet-drift planet-drift-blue"><div className="planet planet-blue"><div className="planet-clouds"/></div></div><div className="planet-drift planet-drift-ringed"><div className="planet-rings"/><div className="planet planet-ringed"/></div><div className="planet-drift planet-drift-small"><div className="planet planet-small"/></div></> : <div className="blackhole"><div className="accretion"/><div className="event-horizon"/><div className="orbit-light"/></div>}
  </div>;
}
