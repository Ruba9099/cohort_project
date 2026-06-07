import { useState } from 'react';

export default function Header() {
  const [open, setOpen] = useState(false);
  return (
    <header className="site-header">
      <div className="container nav-row">
        <div className="logo">Minimalist</div>
        <div className="search">
          <input placeholder="Search watches" />
        </div>
        <div className="icons">
          <button className="icon">🛒</button>
          <button className="hamburger" onClick={() => setOpen(!open)}>
            ☰
          </button>
        </div>
      </div>
      {open && (
        <nav className="mobile-nav">
          <a>Shop</a>
          <a>About</a>
          <a>Contact</a>
        </nav>
      )}
    </header>
  );
}
