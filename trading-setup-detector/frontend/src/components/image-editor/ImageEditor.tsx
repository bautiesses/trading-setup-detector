'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { X, Undo2, Redo2, Save, Trash2 } from 'lucide-react';
import ImageEditorCanvas from './ImageEditorCanvas';
import ImageEditorToolbar from './ImageEditorToolbar';
import { ImageEditorProps, ToolType, CanvasRef } from './types';
import { DEFAULT_COLOR, DEFAULT_STROKE_WIDTH } from './constants';

export default function ImageEditor({
  imageUrl,
  onSave,
  onCancel,
  isOpen,
}: ImageEditorProps) {
  const [tool, setTool] = useState<ToolType>('pencil');
  const [color, setColor] = useState(DEFAULT_COLOR);
  const [strokeWidth, setStrokeWidth] = useState(DEFAULT_STROKE_WIDTH);
  const [canUndo, setCanUndo] = useState(false);
  const [canRedo, setCanRedo] = useState(false);
  const [isReady, setIsReady] = useState(false);

  const canvasRef = useRef<CanvasRef>(null);

  const updateHistoryState = useCallback(() => {
    if (canvasRef.current) {
      setCanUndo(canvasRef.current.canUndo());
      setCanRedo(canvasRef.current.canRedo());
    }
  }, []);

  const handleUndo = useCallback(() => {
    canvasRef.current?.undo();
    setTimeout(updateHistoryState, 50);
  }, [updateHistoryState]);

  const handleRedo = useCallback(() => {
    canvasRef.current?.redo();
    setTimeout(updateHistoryState, 50);
  }, [updateHistoryState]);

  const handleDelete = useCallback(() => {
    canvasRef.current?.deleteSelected();
    setTimeout(updateHistoryState, 50);
  }, [updateHistoryState]);

  const handleSave = useCallback(() => {
    if (canvasRef.current) {
      const dataUrl = canvasRef.current.toDataURL();
      onSave(dataUrl);
    }
  }, [onSave]);

  // Keyboard shortcuts
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      // Ignore if typing in text
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.key === 'Escape') {
        e.preventDefault();
        onCancel();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        handleRedo();
      } else if (e.key === 'Delete' || e.key === 'Backspace') {
        if (tool === 'select') {
          e.preventDefault();
          handleDelete();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onCancel, handleUndo, handleRedo, handleDelete, tool]);

  // Update history state periodically
  useEffect(() => {
    if (!isReady) return;
    const interval = setInterval(updateHistoryState, 200);
    return () => clearInterval(interval);
  }, [isReady, updateHistoryState]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col bg-black/95">
      {/* Header */}
      <div className="flex items-center justify-between p-3 bg-zinc-800 border-b border-zinc-700">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold text-white">Editor de Imagen</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={handleUndo}
              disabled={!canUndo}
              className="p-2 rounded-lg text-zinc-300 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Deshacer (Ctrl+Z)"
            >
              <Undo2 size={20} />
            </button>
            <button
              onClick={handleRedo}
              disabled={!canRedo}
              className="p-2 rounded-lg text-zinc-300 hover:bg-zinc-700 disabled:opacity-40 disabled:cursor-not-allowed"
              title="Rehacer (Ctrl+Y)"
            >
              <Redo2 size={20} />
            </button>
            {tool === 'select' && (
              <button
                onClick={handleDelete}
                className="p-2 rounded-lg text-red-400 hover:bg-zinc-700"
                title="Eliminar seleccionado (Delete)"
              >
                <Trash2 size={20} />
              </button>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleSave}
            className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
          >
            <Save size={18} />
            Guardar
          </button>
          <button
            onClick={onCancel}
            className="p-2 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-700 transition-colors"
            title="Cerrar (Escape)"
          >
            <X size={24} />
          </button>
        </div>
      </div>

      {/* Canvas */}
      <ImageEditorCanvas
        ref={canvasRef}
        imageUrl={imageUrl}
        tool={tool}
        color={color}
        strokeWidth={strokeWidth}
        onReady={() => setIsReady(true)}
      />

      {/* Toolbar */}
      <ImageEditorToolbar
        tool={tool}
        color={color}
        strokeWidth={strokeWidth}
        onToolChange={setTool}
        onColorChange={setColor}
        onStrokeWidthChange={setStrokeWidth}
      />
    </div>
  );
}
