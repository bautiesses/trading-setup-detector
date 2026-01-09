'use client';

import {
  MousePointer2,
  Pencil,
  Minus,
  MoveRight,
  Square,
  Circle,
  Type,
} from 'lucide-react';
import { ToolType } from './types';
import { COLORS, STROKE_WIDTHS } from './constants';
import { cn } from '@/lib/utils';

interface ImageEditorToolbarProps {
  tool: ToolType;
  color: string;
  strokeWidth: number;
  onToolChange: (tool: ToolType) => void;
  onColorChange: (color: string) => void;
  onStrokeWidthChange: (width: number) => void;
}

const tools: { type: ToolType; icon: React.ReactNode; label: string }[] = [
  { type: 'select', icon: <MousePointer2 size={20} />, label: 'Seleccionar' },
  { type: 'pencil', icon: <Pencil size={20} />, label: 'Lapiz' },
  { type: 'line', icon: <Minus size={20} />, label: 'Linea' },
  { type: 'arrow', icon: <MoveRight size={20} />, label: 'Flecha' },
  { type: 'rect', icon: <Square size={20} />, label: 'Rectangulo' },
  { type: 'ellipse', icon: <Circle size={20} />, label: 'Circulo' },
  { type: 'text', icon: <Type size={20} />, label: 'Texto' },
];

export default function ImageEditorToolbar({
  tool,
  color,
  strokeWidth,
  onToolChange,
  onColorChange,
  onStrokeWidthChange,
}: ImageEditorToolbarProps) {
  return (
    <div className="flex flex-wrap items-center gap-4 p-3 bg-zinc-800 border-t border-zinc-700">
      {/* Tools */}
      <div className="flex items-center gap-1">
        {tools.map((t) => (
          <button
            key={t.type}
            onClick={() => onToolChange(t.type)}
            className={cn(
              'p-2 rounded-lg transition-colors',
              tool === t.type
                ? 'bg-blue-600 text-white'
                : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
            )}
            title={t.label}
          >
            {t.icon}
          </button>
        ))}
      </div>

      {/* Divider */}
      <div className="w-px h-8 bg-zinc-600" />

      {/* Colors */}
      <div className="flex items-center gap-1">
        {COLORS.map((c) => (
          <button
            key={c}
            onClick={() => onColorChange(c)}
            className={cn(
              'w-7 h-7 rounded-full border-2 transition-transform',
              color === c ? 'border-white scale-110' : 'border-transparent hover:scale-105'
            )}
            style={{ backgroundColor: c }}
            title={c}
          />
        ))}
      </div>

      {/* Divider */}
      <div className="w-px h-8 bg-zinc-600" />

      {/* Stroke Width */}
      <div className="flex items-center gap-2">
        <span className="text-zinc-400 text-sm">Grosor:</span>
        <div className="flex items-center gap-1">
          {STROKE_WIDTHS.map((w) => (
            <button
              key={w}
              onClick={() => onStrokeWidthChange(w)}
              className={cn(
                'w-8 h-8 rounded-lg flex items-center justify-center transition-colors',
                strokeWidth === w
                  ? 'bg-blue-600 text-white'
                  : 'bg-zinc-700 text-zinc-300 hover:bg-zinc-600'
              )}
              title={`${w}px`}
            >
              <div
                className="rounded-full bg-current"
                style={{ width: w + 4, height: w + 4 }}
              />
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
