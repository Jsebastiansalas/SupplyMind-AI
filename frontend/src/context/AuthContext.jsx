import React, { createContext, useContext, useState, useEffect } from 'react';

export const PERSONAS = {
  judge: {
    id: 'judge',
    name: 'Jurado Evaluador VIP',
    title: 'Juez Principal / Reto Platica 2026',
    org: 'Comité Evaluador Reto Agente',
    avatar: '🏆',
    role: 'judge',
    email: 'jurado.evaluador@platica.mx',
    badge: 'ACCESO MAESTRO VIP'
  },
  cfo: {
    id: 'cfo',
    name: 'Dr. Fernando Morales',
    title: 'Chief Financial Officer (CFO)',
    org: 'Nestlé Supply Chain Global',
    avatar: '👔',
    role: 'cfo',
    email: 'f.morales@nestle-global.com',
    badge: 'DIRECCIÓN FINANCIERA'
  },
  legal: {
    id: 'legal',
    name: 'Lic. Elena Valenzuela',
    title: 'Senior Legal Counsel',
    org: 'Cisco Systems B2B Operations',
    avatar: '⚖️',
    role: 'legal',
    email: 'e.valenzuela@cisco-legal.corp',
    badge: 'ASESORÍA JURÍDICA'
  },
  coo: {
    id: 'coo',
    name: 'Ing. Roberto Méndez',
    title: 'VP Supply Chain Operations',
    org: 'Home Depot Logistics Hub',
    avatar: '📦',
    role: 'coo',
    email: 'r.mendez@homedepot-supply.com',
    badge: 'OPERACIONES & MUELLE'
  }
};

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const saved = localStorage.getItem('supplymind_auth_user');
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      return null;
    }
  });

  useEffect(() => {
    try {
      if (currentUser) {
        localStorage.setItem('supplymind_auth_user', JSON.stringify(currentUser));
      } else {
        localStorage.removeItem('supplymind_auth_user');
      }
    } catch (e) {
      // Ignore storage errors
    }
  }, [currentUser]);

  const loginAsPersona = (personaId) => {
    const persona = PERSONAS[personaId] || PERSONAS.judge;
    setCurrentUser(persona);
    return persona;
  };

  const loginWithCredentials = (email, password) => {
    // Si coincide con alguna persona conocida, asignarla; de lo contrario crear usuario personalizado
    const found = Object.values(PERSONAS).find(p => p.email.toLowerCase() === email.toLowerCase());
    if (found) {
      setCurrentUser(found);
      return found;
    }
    const customUser = {
      id: 'custom_user',
      name: email.split('@')[0].toUpperCase(),
      title: 'Auditor Financiero',
      org: 'Enterprise Clearinghouse',
      avatar: '💼',
      role: 'auditor',
      email: email,
      badge: 'USUARIO CORPORATIVO'
    };
    setCurrentUser(customUser);
    return customUser;
  };

  const logout = () => {
    setCurrentUser(null);
  };

  return (
    <AuthContext.Provider value={{
      currentUser,
      personas: PERSONAS,
      loginAsPersona,
      loginWithCredentials,
      logout,
      isAuthenticated: !!currentUser
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
