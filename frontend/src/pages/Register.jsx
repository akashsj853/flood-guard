import { useState } from 'react'
import { ArrowLeft, UserPlus } from 'lucide-react'

export default function Register({ onSubmit, onBack, onLogin, admin = false }) {
  const [form, setForm] = useState({ username: '', email: '', password: '' })
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)
  async function submit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await onSubmit(form)
    } catch (e) {
      const detail = e.response?.data?.detail
      const validationError = Array.isArray(detail) ? detail.map((item) => item.msg).join(', ') : detail
      setError(validationError || (e.request ? 'Unable to reach the FloodGuard API. Start the backend and try again.' : 'Registration failed. Please try again.'))
    } finally {
      setSubmitting(false)
    }
  }
  const fields = [['username','Username','text'],['email','Email','email'],['password','Password','password']]
  return <main className="min-h-screen bg-[#07141c] text-slate-100 flex items-center justify-center p-6"><form onSubmit={submit} className="w-full max-w-md rounded-3xl border border-teal-900/70 bg-[#0d2029] p-7 shadow-2xl"><button type="button" onClick={onBack} className="text-slate-400 hover:text-white mb-10" aria-label="Back"><ArrowLeft size={19} /></button><UserPlus className="text-teal-300" /><h1 className="font-display text-3xl font-bold mt-4">{admin ? 'Create administrator account' : 'Create your account'}</h1><p className="text-slate-400 mt-2">{admin ? 'Invite-only access for FloodGuard operations.' : 'Start with a personalized public risk view.'}</p>{fields.map(([key,label,type]) => <label key={key} className="block text-sm text-slate-300 mt-5">{label}<input required type={type} minLength={key === 'password' ? 8 : undefined} value={form[key]} onChange={(e) => setForm({ ...form, [key]: e.target.value })} className="auth-input" /></label>)}{error && <p role="alert" aria-live="polite" className="text-rose-300 text-sm mt-4">{error}</p>}<button type="submit" disabled={submitting} className="w-full mt-6 rounded-xl bg-teal-400 text-[#062027] py-3 font-bold disabled:opacity-60 disabled:cursor-not-allowed">{submitting ? 'Creating account...' : admin ? 'Create admin account' : 'Create account'}</button><p className="text-center text-sm text-slate-400 mt-6">Already registered? <button type="button" onClick={onLogin} className="text-teal-300">Sign in</button></p></form></main>
}