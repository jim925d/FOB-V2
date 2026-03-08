import { useState, useEffect } from "react";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

const STORAGE_KEY = "fob_crisis_bar_dismissed";

export default function CrisisBar() {
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    setDismissed(sessionStorage.getItem(STORAGE_KEY) === "true");
  }, []);

  const handleDismiss = () => {
    sessionStorage.setItem(STORAGE_KEY, "true");
    setDismissed(true);
  };

  if (dismissed) return null;

  return (
    <div
      className="w-full py-2 px-4 flex items-center justify-center gap-2 relative text-center"
      style={{ background: "rgba(239,68,68,0.08)" }}
    >
      <span className="text-xs text-destructive">
        Veterans Crisis Line: Dial 988 press 1 · Text 838255
      </span>
      <Button
        variant="ghost"
        size="icon"
        className="absolute right-2 h-6 w-6 text-destructive hover:bg-destructive/10"
        onClick={handleDismiss}
        aria-label="Dismiss"
      >
        <X className="h-3.5 w-3.5" />
      </Button>
    </div>
  );
}
