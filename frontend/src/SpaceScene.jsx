import React from 'react';

// Decorative, CSS-only scene. Motion follows the system accessibility preference.
export default function SpaceScene() {
  return <div className="space-scene" aria-hidden="true">
    <div className="space-stars">{Array.from({length: 32}, (_, i) => <i key={i} style={{left: `${(i * 37 + 11) % 100}%`, top: `${(i * 23 + 7) % 100}%`, animationDelay: `${i * -.31}s`}}/>)}</div>
    <div className="blackhole"><div className="accretion"/><div className="event-horizon"/><div className="orbit-light"/></div>
  </div>;
}
