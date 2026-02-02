"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface AuthContextType {
    authenticated: boolean;
    setAuthenticated: (value: boolean) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ initial, children }: { initial: boolean, children: ReactNode }) {
    const [authenticated, setAuthenticated] = useState<boolean>(initial);

    return (
        <AuthContext.Provider value={{ authenticated, setAuthenticated }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
}