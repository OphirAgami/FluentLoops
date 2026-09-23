import { useEffect, useState, type FormEvent } from 'react'

const API_URL = 'http://localhost:8000'

type User = {
    id: number
    email: string
}
type Mode = 'register' | 'login'

async function errorMessage(response: Response): Promise<string> {
    try {
        const data = (await response.json()) as { detail?: unknown }
        if (typeof data.detail === 'string') return data.detail
    } catch {
        return `Request failed (${response.status})`
    }
    return `Request failed (${response.status})`
}

export default function App() {
    const [mode, setMode] = useState<Mode>('register')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [user, setUser] = useState<User | null>(null)
    const [message, setMessage] = useState('Checking your session...')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function restoreSession() {
            try {
                const response = await fetch(`${API_URL}/auth/me`, {
                    credentials: 'include',
                })
                if (response.status === 401) {
                    setMessage('Create an account or sign in.')
                    return
                }
                if (!response.ok) throw new Error(await errorMessage(response))
                const signedInUser = (await response.json()) as User
                setUser(signedInUser)
                setMessage('Your session was restored.')
            } catch (error) {
                setMessage(error instanceof Error ? error.message : 'Could not reach the server.')
            } finally {
                setLoading(false)
            }
        }
        void restoreSession()
    }, [])

    async function submitAuth(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setLoading(true)
        setMessage(mode === 'register' ? 'Creating account...' : 'Signing in...')
        try {
            const response = await fetch(`${API_URL}/auth/${mode}`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password }),
            })
            if (!response.ok) throw new Error(await errorMessage(response))
            const signedInUser = (await response.json()) as User
            setUser(signedInUser)
            setPassword('')
            setMessage(mode === 'register' ? 'Account created.' : 'Signed in.')
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Request failed.')
        } finally {
            setLoading(false)
        }
    }

    async function logout() {
        setLoading(true)
        setMessage('Signing out...')
        try {
            const response = await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            })
            if (!response.ok) throw new Error(await errorMessage(response))
            setUser(null)
            setEmail('')
            setPassword('')
            setMessage('Signed out.')
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Could not sign out.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <main className="shell">
            <section className="card" aria-labelledby="page-title">
                <p className="eyebrow">Adaptive English practice</p>
                <h1 id="page-title">FluentLoop</h1>
                <p className="intro">Your account will keep your learning journey separate and safe.</p>

                {user ? (
                    <div className="signed-in">
                        <p className="label">Signed in as</p>
                        <p className="email">{user.email}</p>
                        <button type="button" onClick={logout} disabled={loading}>
                            {loading ? 'Please wait...' : 'Log out'}
                        </button>
                    </div>
                ) : (
                    <>
                        <div className="mode-switch" aria-label="Choose account action">
                            <button
                                type="button"
                                className={mode === 'register' ? 'active' : ''}
                                onClick={() => setMode('register')}
                                disabled={loading}
                            >
                                Register
                            </button>
                            <button
                                type="button"
                                className={mode === 'login' ? 'active' : ''}
                                onClick={() => setMode('login')}
                                disabled={loading}
                            >
                                Log in
                            </button>
                        </div>

                        <form onSubmit={submitAuth}>
                            <label htmlFor="email">Email</label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={(event) => setEmail(event.target.value)}
                                autoComplete="email"
                                required
                            />
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
                                minLength={8}
                                maxLength={128}
                                required
                            />
                            <button type="submit" disabled={loading}>
                                {loading ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Log in'}
                            </button>
                        </form>
                    </>
                )}
                <p className="status" role="status" aria-live="polite">
                    {message}
                </p>
            </section>
        </main>
    )
}