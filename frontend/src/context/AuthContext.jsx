import { createContext, useContext, useEffect, useState } from 'react'
import * as api from '../services/api'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getCurrentUser().then(setUser).catch(() => setUser(null)).finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const onUnauthorized = () => setUser(null)
    window.addEventListener('floodguard:unauthorized', onUnauthorized)
    return () => window.removeEventListener('floodguard:unauthorized', onUnauthorized)
  }, [])

  async function login(credentials) {
    const result = await api.loginUser(credentials)
    setUser(result.user)
    return result.user
  }

  async function loginAdmin(credentials) {
    const result = await api.adminLogin(credentials)
    setUser(result.user)
    return result.user
  }

  async function registerAdmin(payload) {
    const result = await api.adminRegister(payload)
    setUser(result.user)
    return result.user
  }

  async function register(payload) {
    const result = await api.registerUser(payload)
    setUser(result.user)
    return result.user
  }

  async function logout() {
    await api.logoutUser().catch(() => {})
    setUser(null)
  }

  return <AuthContext.Provider value={{ user, loading, login, loginAdmin, register, registerAdmin, logout, setUser }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const value = useContext(AuthContext)
  if (!value) throw new Error('useAuth must be used inside AuthProvider')
  return value
}