import * as React from "react";
import { ChevronDown, X } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/**
 * SearchableSelect — Popover + Command for searchable, keyboard-navigable select.
 * Props: options, value, onChange, placeholder, multi, grouped, allowCustom, label, error, required
 */
export function SearchableSelect({
  options = [],
  value,
  onChange,
  placeholder = "Select...",
  multi = false,
  grouped = false,
  allowCustom = false,
  label,
  error,
  required,
  className,
}) {
  const [open, setOpen] = React.useState(false);
  const [search, setSearch] = React.useState("");

  const selectedValues = Array.isArray(value) ? value : value != null ? [value] : [];
  const optionsList = grouped
    ? options.flatMap((g) => (g.options || g).map((o) => ({ ...o, group: g.label || g.heading })))
    : options;

  const displayLabel = (opt) => (typeof opt === "object" && opt !== null ? opt.label ?? opt.value : String(opt));
  const optionValue = (opt) => (typeof opt === "object" && opt !== null ? opt.value : opt);

  const handleSelect = (val) => {
    if (multi) {
      const next = selectedValues.includes(val)
        ? selectedValues.filter((v) => v !== val)
        : [...selectedValues, val];
      onChange?.(next);
    } else {
      onChange?.(val);
      setOpen(false);
    }
  };

  const removeOne = (e, val) => {
    e.stopPropagation();
    if (multi) onChange?.(selectedValues.filter((v) => v !== val));
  };

  const triggerLabel = multi
    ? selectedValues.length
      ? `${selectedValues.length} selected`
      : placeholder
    : selectedValues.length
      ? displayLabel(optionsList.find((o) => optionValue(o) === selectedValues[0]))
      : placeholder;

  return (
    <div className={cn("space-y-1.5", className)}>
      {label && (
        <label className="text-sm font-medium text-[--color-text-secondary]">
          {label}
          {required && <span className="text-destructive ml-0.5">*</span>}
        </label>
      )}
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <button
            type="button"
            className={cn(
              "flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
              error && "border-destructive focus:ring-destructive"
            )}
          >
            <span className="flex flex-wrap items-center gap-1 truncate">
              {multi && selectedValues.length > 0 ? (
                selectedValues.map((val) => (
                  <Badge
                    key={val}
                    variant="secondary"
                    className="mr-1 gap-0.5 rounded px-1.5 py-0"
                  >
                    {displayLabel(optionsList.find((o) => optionValue(o) === val))}
                    <button
                      type="button"
                      onClick={(e) => removeOne(e, val)}
                      className="ml-0.5 rounded-full p-0.5 hover:bg-muted"
                      aria-label={`Remove ${val}`}
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </Badge>
                ))
              ) : (
                triggerLabel
              )}
            </span>
            <ChevronDown className="h-4 w-4 shrink-0 opacity-50" />
          </button>
        </PopoverTrigger>
        <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0" align="start">
          <Command shouldFilter={true}>
            <CommandInput
              placeholder="Search..."
              value={search}
              onValueChange={setSearch}
            />
            <CommandList>
              <CommandEmpty>No results found.</CommandEmpty>
              {grouped ? (
                options.map((group) => (
                  <CommandGroup key={group.value ?? group.label ?? group.heading} heading={group.label ?? group.heading}>
                    {(group.options || group).map((opt) => {
                      const val = optionValue(opt);
                      const isSelected = selectedValues.includes(val);
                      return (
                        <CommandItem
                          key={val}
                          value={displayLabel(opt)}
                          onSelect={() => handleSelect(val)}
                        >
                          {displayLabel(opt)}
                          {isSelected && " ✓"}
                        </CommandItem>
                      );
                    })}
                  </CommandGroup>
                ))
              ) : (
                <CommandGroup>
                  {optionsList.map((opt) => {
                    const val = optionValue(opt);
                    const isSelected = selectedValues.includes(val);
                    return (
                      <CommandItem
                        key={val}
                        value={displayLabel(opt)}
                        onSelect={() => handleSelect(val)}
                      >
                        {displayLabel(opt)}
                        {isSelected && " ✓"}
                      </CommandItem>
                    );
                  })}
                  {allowCustom && search.trim() && (
                    <CommandItem
                      value={`Add "${search.trim()}"`}
                      onSelect={() => {
                        onChange?.(search.trim());
                        setOpen(false);
                      }}
                    >
                      Add &quot;{search.trim()}&quot;
                    </CommandItem>
                  )}
                </CommandGroup>
              )}
            </CommandList>
          </Command>
        </PopoverContent>
      </Popover>
      {error && <p className="text-xs text-destructive">{error}</p>}
    </div>
  );
}
