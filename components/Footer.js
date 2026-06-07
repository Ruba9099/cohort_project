export default function Footer() {
  return (
    <footer className="site-footer">
      <div className="container footer-top">
        <div className="newsletter">
          <h4>Join the list</h4>
          <p>Get early access to new releases and offers.</p>
          <form className="subscribe">
            <input placeholder="Email address" />
            <button className="btn">Subscribe</button>
          </form>
        </div>
        <div className="links">
          <a>About</a>
          <a>FAQs</a>
          <a>Contact</a>
        </div>
      </div>
      <div className="container footer-bottom">
        <div>© {new Date().getFullYear()} Minimalist</div>
        <div className="social">Instagram · Twitter · Facebook</div>
      </div>
    </footer>
  );
}
