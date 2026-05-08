import { Lightbulb } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

interface InsightCardProps {
  insight: string;
  suggestions: string[];
}

export default function InsightCard({ insight, suggestions }: InsightCardProps) {
  return (
    <Card className="bg-blue-50 border-blue-100">
      <CardContent className="p-4 space-y-2">
        <div className="flex items-start gap-2">
          <Lightbulb size={16} className="text-blue-600 mt-0.5 shrink-0" />
          <p className="text-sm text-gray-800">{insight}</p>
        </div>
        {suggestions.length > 0 && (
          <ul className="ml-6 space-y-1">
            {suggestions.map((s, i) => (
              <li key={i} className="text-sm text-gray-600 list-disc">
                {s}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
