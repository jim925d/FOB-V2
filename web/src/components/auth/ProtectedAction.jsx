import { useAuth } from '@/contexts/AuthContext';
import AuthModal from './AuthModal';
import { useState } from 'react';

export function ProtectedAction({ children, message, onAuthenticated }) {
  const { isAuthenticated } = useAuth();
  const [showAuth, setShowAuth] = useState(false);
  const [pendingAction, setPendingAction] = useState(false);

  const handleClick = () => {
    if (isAuthenticated) {
      onAuthenticated?.();
    } else {
      setPendingAction(true);
      setShowAuth(true);
    }
  };

  const handleAuthSuccess = () => {
    setShowAuth(false);
    if (pendingAction) {
      onAuthenticated?.();
      setPendingAction(false);
    }
  };

  return (
    <>
      {children({ onClick: handleClick })}
      <AuthModal
        open={showAuth}
        onOpenChange={setShowAuth}
        contextMessage={message}
        defaultTab="signin"
        onSuccess={handleAuthSuccess}
      />
    </>
  );
}
