import { useState } from "react";
import { ChevronDown, ChevronRight, Copy, Check } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Badge } from "@/components/ui/badge";

interface SqlPreviewProps {
  sql: string;
  executionMs?: number | null;
}

export default function SqlPreview({ sql, executionMs }: SqlPreviewProps) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(sql);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-2">
      <div className="flex items-center gap-2">
        <CollapsibleTrigger className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700">
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
          SQL
        </CollapsibleTrigger>
        {executionMs != null && (
          <Badge variant="secondary" className="text-[10px]">
            {executionMs}ms
          </Badge>
        )}
      </div>
      <CollapsibleContent>
        <div className="relative mt-1 rounded-md bg-gray-900 p-3">
          <button
            onClick={handleCopy}
            className="absolute top-2 right-2 text-gray-400 hover:text-white"
            title="Copy SQL"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
          </button>
          <pre className="text-xs text-gray-100 overflow-x-auto whitespace-pre-wrap">
            {sql}
          </pre>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}
