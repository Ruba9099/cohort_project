import Head from 'next/head';
import { useEffect, useState } from 'react';
import StoreLayout from '../components/StoreLayout';
import { clearAuth, getStoredAuth, requestApi, saveAuth } from '../lib/store';

export default function Account() {
  const [auth, setAuth] = useState({ token: '', user: null });
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [message, setMessage] = useState('');

  useEffect(() => { setAuth(getStoredAuth()); }, []);

  async function submit(e) {
    e.preventDefault();
    setMessage('');
    try {
      const body = mode === 'signup' ? form : { email: form.email, password: form.password };
      const data = await requestApi(`/api/auth/${mode}`, { method: 'POST', body: JSON.stringify(body) });
      saveAuth({ token: data.token, user: data.user });
      setAuth({ token: data.token, user: data.user });
      setMessage(`Signed in as ${data.user.name}.`);
    } catch (err) { setMessage(err.message); }
  }

  async function logout() {
    try { await requestApi('/api/auth/logout', { method: 'POST' }, auth.token); } catch {}
    clearAuth();
    setAuth({ token: '', user: null });
    setMessage('Signed out.');
  }

  return (
    <StoreLayout>
      <Head><title>Account | Brand Store</title></Head>
      <main>
        <section className="section" style={{ maxWidth: 480, margin: '0 auto' }}>
          <div className="section-heading compact">
            <p className="eyebrow">Account</p>
            <h2>{auth.user ? 'Signed in' : 'Login or sign up'}</h2>
          </div>
          {message && <div className="status-message">{message}</div>}
          {auth.user ? (
            <div className="panel" style={{ padding: 24 }}>
              <p style={{ marginTop: 0 }}><strong>{auth.user.name}</strong><br /><span style={{ color: 'var(--muted)' }}>{auth.user.email}</span></p>
              <button className="button secondary" onClick={logout}>Sign out</button>
            </div>
          ) : (
            <div className="panel" style={{ padding: 24 }}>
              <div className="segmented" style={{ marginBottom: 18 }}>
                <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Login</button>
                <button className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Sign up</button>
              </div>
              <form className="form" onSubmit={submit}>
                {mode === 'signup' && <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>}
                <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required /></label>
                <label>Password<input type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required /></label>
                <button className="button primary full">{mode === 'signup' ? 'Create account' : 'Login'}</button>
              </form>
            </div>
          )}
        </section>
      </main>
    </StoreLayout>
  );
}
