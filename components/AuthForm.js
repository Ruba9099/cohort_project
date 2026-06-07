import { useState } from 'react';
import { requestApi, saveAuth } from '../lib/store';

export default function AuthForm({ onAuth, onMessage }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  async function submitAuth(event) {
    event.preventDefault();

    try {
      const body = mode === 'signup' ? form : { email: form.email, password: form.password };
      const data = await requestApi(`/api/auth/${mode}`, {
        method: 'POST',
        body: JSON.stringify(body),
      });
      saveAuth({ token: data.token, user: data.user });
      setForm({ name: '', email: '', password: '' });
      onAuth?.({ token: data.token, user: data.user });
      onMessage?.(`Signed in as ${data.user.name}.`);
    } catch (error) {
      onMessage?.(error.message);
    }
  }

  return (
    <form className="form" onSubmit={submitAuth}>
      <div className="segmented">
        <button className={mode === 'login' ? 'active' : ''} type="button" onClick={() => setMode('login')}>
          Login
        </button>
        <button className={mode === 'signup' ? 'active' : ''} type="button" onClick={() => setMode('signup')}>
          Sign up
        </button>
      </div>
      {mode === 'signup' && (
        <label>
          Name
          <input value={form.name} onChange={(event) => setForm({ ...form, name: event.target.value })} required />
        </label>
      )}
      <label>
        Email
        <input
          type="email"
          value={form.email}
          onChange={(event) => setForm({ ...form, email: event.target.value })}
          required
        />
      </label>
      <label>
        Password
        <input
          type="password"
          value={form.password}
          onChange={(event) => setForm({ ...form, password: event.target.value })}
          required
        />
      </label>
      <button className="button primary full" type="submit">
        {mode === 'signup' ? 'Create account' : 'Login'}
      </button>
    </form>
  );
}
