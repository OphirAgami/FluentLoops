import { useEffect, useState, type FormEvent } from 'react'

const API_URL = 'http://localhost:8000'
const TARGET_BATCH_SIZE = 5

type User = {
    id: number
    email: string
    xp: number
    streak_days: number
}

type AuthMode = 'register' | 'login'
type Screen = 'levels' | 'packs' | 'slider' | 'preview'

type LevelSummary = {
    level: string
    total_words: number
    completed_words: number
}

type PackSummary = {
    pack_number: number
    total_words: number
    completed_words: number
    learning_words: number
}

type PackWord = {
    id: number
    word: string
    cefr_level: string
    pack_number: number
    meaning_he: string
    example_sentence: string
    status: 'known' | 'learning' | 'mastered' | null
}

const LEVEL_TITLES: Record<string, string> = {
    A1: 'Beginner',
    A2: 'Elementary',
    B1: 'Intermediate',
    B2: 'Upper-Int',
    C1: 'Advanced',
    C2: 'Mastery',
}

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
    const [mode, setMode] = useState<AuthMode>('login')
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [user, setUser] = useState<User | null>(null)
    const [message, setMessage] = useState('Checking your session...')
    const [loading, setLoading] = useState(true)

    // Navigation & learning state
    const [screen, setScreen] = useState<Screen>('levels')
    const [levels, setLevels] = useState<LevelSummary[]>([])
    const [selectedLevel, setSelectedLevel] = useState<string>('B1')
    const [packs, setPacks] = useState<PackSummary[]>([])
    const [selectedPack, setSelectedPack] = useState<number>(1)
    const [unseenWords, setUnseenWords] = useState<PackWord[]>([])
    const [currentIndex, setCurrentIndex] = useState<number>(0)
    const [collectedWords, setCollectedWords] = useState<PackWord[]>([])

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
                setMessage('')
                await loadLevels()
            } catch (error) {
                setMessage(error instanceof Error ? error.message : 'Could not reach the server.')
            } finally {
                setLoading(false)
            }
        }
        void restoreSession()
    }, [])

    async function loadLevels() {
        const response = await fetch(`${API_URL}/levels`, { credentials: 'include' })
        if (!response.ok) throw new Error(await errorMessage(response))
        const data = (await response.json()) as LevelSummary[]
        setLevels(data)
    }

    async function openLevel(level: string) {
        setLoading(true)
        setMessage('')
        try {
            const response = await fetch(`${API_URL}/levels/${level}/packs`, {
                credentials: 'include',
            })
            if (!response.ok) throw new Error(await errorMessage(response))
            const data = (await response.json()) as PackSummary[]
            setSelectedLevel(level)
            setPacks(data)
            setScreen('packs')
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Could not load packs.')
        } finally {
            setLoading(false)
        }
    }

    async function openPack(packNumber: number) {
        setLoading(true)
        setMessage('')
        try {
            const response = await fetch(
                `${API_URL}/levels/${selectedLevel}/packs/${packNumber}/words`,
                { credentials: 'include' },
            )
            if (!response.ok) throw new Error(await errorMessage(response))
            const allWords = (await response.json()) as PackWord[]

            const alreadyLearning = allWords.filter((w) => w.status === 'learning')
            const remainingUnseen = allWords.filter((w) => w.status === null)

            setSelectedPack(packNumber)
            setCollectedWords(alreadyLearning.slice(0, TARGET_BATCH_SIZE))
            setUnseenWords(remainingUnseen)
            setCurrentIndex(0)

            if (alreadyLearning.length >= TARGET_BATCH_SIZE || (remainingUnseen.length === 0 && alreadyLearning.length > 0)) {
                setScreen('preview')
            } else if (remainingUnseen.length === 0) {
                setMessage('You already completed every word in this pack!')
            } else {
                setScreen('slider')
            }
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Could not load words.')
        } finally {
            setLoading(false)
        }
    }

    async function handleSwipe(decision: 'known' | 'learning') {
        const currentWord = unseenWords[currentIndex]
        if (!currentWord || loading) return

        setLoading(true)
        try {
            const response = await fetch(`${API_URL}/words/${currentWord.id}/swipe`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ status: decision }),
            })
            if (!response.ok) throw new Error(await errorMessage(response))

            const updatedCollected =
                decision === 'learning' ? [...collectedWords, currentWord] : collectedWords
            setCollectedWords(updatedCollected)

            const nextIndex = currentIndex + 1
            const reachedBatchGoal = updatedCollected.length >= TARGET_BATCH_SIZE
            const finishedDeck = nextIndex >= unseenWords.length

            if (reachedBatchGoal || (finishedDeck && updatedCollected.length > 0)) {
                setScreen('preview')
            } else if (finishedDeck) {
                await openLevel(selectedLevel)
                setMessage(`Pack ${selectedPack} completed!`)
            } else {
                setCurrentIndex(nextIndex)
            }
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Could not save word choice.')
        } finally {
            setLoading(false)
        }
    }

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
            setMessage('')
            setScreen('levels')
            await loadLevels()
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Request failed.')
        } finally {
            setLoading(false)
        }
    }

    async function logout() {
        setLoading(true)
        try {
            const response = await fetch(`${API_URL}/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            })
            if (!response.ok) throw new Error(await errorMessage(response))
            setUser(null)
            setEmail('')
            setPassword('')
            setScreen('levels')
            setMessage('Signed out.')
        } catch (error) {
            setMessage(error instanceof Error ? error.message : 'Could not sign out.')
        } finally {
            setLoading(false)
        }
    }

    if (!user) {
        return (
            <main className="shell">
                <section className="card auth-card" aria-labelledby="page-title">
                    <div className="brand-header">
                        <span className="logo-badge" aria-hidden="true">🗣️</span>
                        <div>
                            <p className="eyebrow">Adaptive English Practice</p>
                            <h1 id="page-title">FluentLoop</h1>
                        </div>
                    </div>
                    <p className="intro">Discover unfamiliar words and turn them into active speaking fluency.</p>

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
                        <button type="submit" className="primary-btn" disabled={loading}>
                            {loading ? 'Please wait...' : mode === 'register' ? 'Create account' : 'Log in'}
                        </button>
                    </form>

                    {message && (
                        <p className="status" role="status" aria-live="polite">
                            {message}
                        </p>
                    )}
                </section>
            </main>
        )
    }

    const activeWord = unseenWords[currentIndex]

    return (
        <main className="app-shell">
            <header className="topbar">
                <button
                    type="button"
                    className="brand-link"
                    onClick={() => {
                        void loadLevels()
                        setScreen('levels')
                        setMessage('')
                    }}
                >
                    <span className="logo-badge small" aria-hidden="true">🗣️</span>
                    <span className="brand-name">FluentLoop</span>
                </button>

                <div className="stats-bar">
                    <span className="stat-pill streak">🔥 {user.streak_days} day streak</span>
                    <span className="stat-pill xp">⭐ {user.xp} XP</span>
                    <button type="button" className="ghost-btn" onClick={logout} disabled={loading}>
                        Log out
                    </button>
                </div>
            </header>

            <section className="workspace-card">
                {screen === 'levels' && (
                    <>
                        <div className="section-head">
                            <p className="eyebrow">Step 1 · Choose any CEFR level</p>
                            <h2>Select a Level to Practice</h2>
                        </div>

                        <div className="levels-grid">
                            {levels.map((item) => {
                                const percent =
                                    item.total_words > 0
                                        ? Math.round((item.completed_words / item.total_words) * 100)
                                        : 0
                                return (
                                    <button
                                        key={item.level}
                                        type="button"
                                        className="level-tile"
                                        onClick={() => void openLevel(item.level)}
                                        disabled={loading}
                                    >
                                        <span className="level-code">{item.level}</span>
                                        <span className="level-title">{LEVEL_TITLES[item.level]}</span>
                                        <div className="progress-track">
                                            <div className="progress-fill" style={{ width: `${percent}%` }} />
                                        </div>
                                        <span className="progress-caption">
                                            {item.completed_words} / {item.total_words} words
                                        </span>
                                    </button>
                                )
                            })}
                        </div>
                    </>
                )}

                {screen === 'packs' && (
                    <>
                        <div className="nav-row">
                            <button
                                type="button"
                                className="back-btn"
                                onClick={() => {
                                    void loadLevels()
                                    setScreen('levels')
                                    setMessage('')
                                }}
                            >
                                ← All Levels
                            </button>
                            <span className="level-badge">Level {selectedLevel}</span>
                        </div>

                        <div className="section-head">
                            <p className="eyebrow">Step 2 · Pick a word group</p>
                            <h2>{selectedLevel} Word Packs</h2>
                        </div>

                        <div className="packs-list">
                            {packs.map((pack) => {
                                const percent =
                                    pack.total_words > 0
                                        ? Math.round((pack.completed_words / pack.total_words) * 100)
                                        : 0
                                return (
                                    <button
                                        key={pack.pack_number}
                                        type="button"
                                        className="pack-card"
                                        onClick={() => void openPack(pack.pack_number)}
                                        disabled={loading}
                                    >
                                        <div className="pack-top">
                                            <span className="pack-title">Pack {pack.pack_number}</span>
                                            <span className="pack-count">
                                                {pack.completed_words} / {pack.total_words} learned
                                            </span>
                                        </div>
                                        <div className="progress-track">
                                            <div className="progress-fill" style={{ width: `${percent}%` }} />
                                        </div>
                                    </button>
                                )
                            })}
                        </div>
                    </>
                )}

                {screen === 'slider' && activeWord && (
                    <>
                        <div className="nav-row">
                            <button
                                type="button"
                                className="back-btn"
                                onClick={() => void openLevel(selectedLevel)}
                            >
                                ← Back to Packs
                            </button>
                            <span className="batch-pill">
                                Collected: {collectedWords.length} / {TARGET_BATCH_SIZE}
                            </span>
                        </div>

                        <div className="section-head center">
                            <p className="eyebrow">
                                {selectedLevel} · Pack {selectedPack}
                            </p>
                            <h2>Swipe right on 5 unfamiliar words</h2>
                            <p className="subtitle">
                                Filter out words you already know so we only practice new ones.
                            </p>
                        </div>

                        <div className="word-slider-card">
                            <span className="card-counter">
                                Card {currentIndex + 1} of {unseenWords.length}
                            </span>
                            <h3 className="big-word">{activeWord.word}</h3>
                        </div>

                        <div className="swipe-actions">
                            <button
                                type="button"
                                className="swipe-btn known"
                                onClick={() => void handleSwipe('known')}
                                disabled={loading}
                            >
                                ← I know this
                            </button>
                            <button
                                type="button"
                                className="swipe-btn learning"
                                onClick={() => void handleSwipe('learning')}
                                disabled={loading}
                            >
                                Don&apos;t know yet →
                            </button>
                        </div>
                    </>
                )}

                {screen === 'preview' && (
                    <>
                        <div className="nav-row">
                            <button
                                type="button"
                                className="back-btn"
                                onClick={() => void openLevel(selectedLevel)}
                            >
                                ← Back to Packs
                            </button>
                            <span className="batch-pill">
                                {collectedWords.length} target words ready
                            </span>
                        </div>

                        <div className="section-head">
                            <p className="eyebrow">Step 3 · Review your target words</p>
                            <h2>Words Selected for Speaking Practice</h2>
                        </div>

                        <div className="preview-list">
                            {collectedWords.map((item) => (
                                <div key={item.id} className="preview-item">
                                    <div className="preview-word-row">
                                        <strong>{item.word}</strong>
                                        <span className="hebrew-meaning">{item.meaning_he}</span>
                                    </div>
                                    <p className="example-line">{item.example_sentence}</p>
                                </div>
                            ))}
                        </div>

                        <button
                            type="button"
                            className="primary-btn full-width"
                            onClick={() => void openLevel(selectedLevel)}
                        >
                            Save Selection &amp; Return to Packs (Speaking Mic Next!)
                        </button>
                    </>
                )}

                {message && (
                    <p className="status" role="status" aria-live="polite">
                        {message}
                    </p>
                )}
            </section>
        </main>
    )
}