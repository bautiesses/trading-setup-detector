export type ToolType = 'select' | 'pencil' | 'line' | 'arrow' | 'rect' | 'ellipse' | 'text';

export interface EditorState {
  tool: ToolType;
  color: string;
  strokeWidth: number;
  fontSize: number;
}

export interface ImageEditorProps {
  imageUrl: string;
  onSave: (editedBase64: string) => void;
  onCancel: () => void;
  isOpen: boolean;
}

export interface CanvasRef {
  toDataURL: () => string;
  undo: () => void;
  redo: () => void;
  canUndo: () => boolean;
  canRedo: () => boolean;
  deleteSelected: () => void;
}
