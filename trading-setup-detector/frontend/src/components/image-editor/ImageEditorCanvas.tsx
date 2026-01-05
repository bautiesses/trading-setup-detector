'use client';

import { useEffect, useRef, useImperativeHandle, forwardRef, useCallback } from 'react';
import * as fabric from 'fabric';
import { ToolType, CanvasRef } from './types';
import { FONT_FAMILY, DEFAULT_FONT_SIZE } from './constants';

interface ImageEditorCanvasProps {
  imageUrl: string;
  tool: ToolType;
  color: string;
  strokeWidth: number;
  onReady?: () => void;
}

const ImageEditorCanvas = forwardRef<CanvasRef, ImageEditorCanvasProps>(
  ({ imageUrl, tool, color, strokeWidth, onReady }, ref) => {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const fabricRef = useRef<fabric.Canvas | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const historyRef = useRef<string[]>([]);
    const historyIndexRef = useRef<number>(-1);
    const isDrawingRef = useRef(false);
    const startPointRef = useRef<{ x: number; y: number } | null>(null);
    const activeShapeRef = useRef<fabric.Object | null>(null);

    const saveHistory = useCallback(() => {
      if (!fabricRef.current) return;
      const json = JSON.stringify(fabricRef.current.toJSON());

      // Remove future history if we're not at the end
      if (historyIndexRef.current < historyRef.current.length - 1) {
        historyRef.current = historyRef.current.slice(0, historyIndexRef.current + 1);
      }

      historyRef.current.push(json);
      historyIndexRef.current = historyRef.current.length - 1;

      // Limit history to 50 states
      if (historyRef.current.length > 50) {
        historyRef.current.shift();
        historyIndexRef.current--;
      }
    }, []);

    // Initialize canvas
    useEffect(() => {
      if (!canvasRef.current || !containerRef.current) return;

      const container = containerRef.current;
      const canvas = new fabric.Canvas(canvasRef.current, {
        selection: true,
        preserveObjectStacking: true,
      });

      fabricRef.current = canvas;

      // Load background image after a small delay to ensure container has dimensions
      const loadImage = () => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload = () => {
          if (!fabricRef.current) return;

          const containerWidth = container.clientWidth || 800;
          const containerHeight = container.clientHeight || 600;

          // Calculate scale to fit image in container (allow scaling up)
          const scaleX = containerWidth / img.width;
          const scaleY = containerHeight / img.height;
          const scale = Math.min(scaleX, scaleY) * 0.9; // 90% of container for padding

          const canvasWidth = Math.max(img.width * scale, 100);
          const canvasHeight = Math.max(img.height * scale, 100);

          try {
            fabricRef.current.setDimensions({ width: canvasWidth, height: canvasHeight });

            const fabricImage = new fabric.FabricImage(img, {
              scaleX: scale,
              scaleY: scale,
              selectable: false,
              evented: false,
            });

            fabricRef.current.backgroundImage = fabricImage;
            fabricRef.current.renderAll();

            // Save initial state
            saveHistory();
            onReady?.();
          } catch (error) {
            console.error('Error setting up canvas:', error);
          }
        };
        img.onerror = () => {
          console.error('Error loading image');
        };
        img.src = imageUrl;
      };

      // Small delay to ensure DOM is ready
      setTimeout(loadImage, 100);

      // Object modification handler
      canvas.on('object:modified', saveHistory);
      canvas.on('path:created', saveHistory);

      return () => {
        canvas.dispose();
        fabricRef.current = null;
      };
    }, [imageUrl, saveHistory, onReady]);

    // Handle tool changes
    useEffect(() => {
      const canvas = fabricRef.current;
      if (!canvas) return;

      // Reset drawing mode
      canvas.isDrawingMode = false;
      canvas.selection = false;
      canvas.defaultCursor = 'crosshair';

      // Remove previous event listeners
      canvas.off('mouse:down');
      canvas.off('mouse:move');
      canvas.off('mouse:up');

      if (tool === 'select') {
        canvas.selection = true;
        canvas.defaultCursor = 'default';
        canvas.forEachObject((obj) => {
          obj.selectable = true;
          obj.evented = true;
        });
      } else if (tool === 'pencil') {
        canvas.isDrawingMode = true;
        canvas.freeDrawingBrush = new fabric.PencilBrush(canvas);
        canvas.freeDrawingBrush.color = color;
        canvas.freeDrawingBrush.width = strokeWidth;
      } else if (tool === 'text') {
        canvas.defaultCursor = 'text';
        canvas.on('mouse:down', (e) => {
          if (e.target) return; // Don't add text on existing objects

          const pointer = canvas.getViewportPoint(e.e);
          const text = new fabric.IText('Texto', {
            left: pointer.x,
            top: pointer.y,
            fontFamily: FONT_FAMILY,
            fontSize: DEFAULT_FONT_SIZE,
            fill: color,
            selectable: true,
          });

          canvas.add(text);
          canvas.setActiveObject(text);
          text.enterEditing();
          text.selectAll();
          saveHistory();
        });
      } else {
        // Shape tools (line, arrow, rect, ellipse)
        canvas.forEachObject((obj) => {
          obj.selectable = false;
          obj.evented = false;
        });

        canvas.on('mouse:down', (e) => {
          if (isDrawingRef.current) return;

          isDrawingRef.current = true;
          const pointer = canvas.getViewportPoint(e.e);
          startPointRef.current = { x: pointer.x, y: pointer.y };

          let shape: fabric.Object | null = null;

          if (tool === 'line') {
            shape = new fabric.Line([pointer.x, pointer.y, pointer.x, pointer.y], {
              stroke: color,
              strokeWidth: strokeWidth,
              selectable: false,
            });
          } else if (tool === 'arrow') {
            shape = new fabric.Line([pointer.x, pointer.y, pointer.x, pointer.y], {
              stroke: color,
              strokeWidth: strokeWidth,
              selectable: false,
            });
          } else if (tool === 'rect') {
            shape = new fabric.Rect({
              left: pointer.x,
              top: pointer.y,
              width: 0,
              height: 0,
              fill: 'transparent',
              stroke: color,
              strokeWidth: strokeWidth,
              selectable: false,
            });
          } else if (tool === 'ellipse') {
            shape = new fabric.Ellipse({
              left: pointer.x,
              top: pointer.y,
              rx: 0,
              ry: 0,
              fill: 'transparent',
              stroke: color,
              strokeWidth: strokeWidth,
              selectable: false,
            });
          }

          if (shape) {
            canvas.add(shape);
            activeShapeRef.current = shape;
          }
        });

        canvas.on('mouse:move', (e) => {
          if (!isDrawingRef.current || !startPointRef.current || !activeShapeRef.current) return;

          const pointer = canvas.getViewportPoint(e.e);
          const start = startPointRef.current;

          if (tool === 'line' || tool === 'arrow') {
            const line = activeShapeRef.current as fabric.Line;
            line.set({ x2: pointer.x, y2: pointer.y });
          } else if (tool === 'rect') {
            const rect = activeShapeRef.current as fabric.Rect;
            const width = pointer.x - start.x;
            const height = pointer.y - start.y;

            rect.set({
              left: width > 0 ? start.x : pointer.x,
              top: height > 0 ? start.y : pointer.y,
              width: Math.abs(width),
              height: Math.abs(height),
            });
          } else if (tool === 'ellipse') {
            const ellipse = activeShapeRef.current as fabric.Ellipse;
            const rx = Math.abs(pointer.x - start.x) / 2;
            const ry = Math.abs(pointer.y - start.y) / 2;

            ellipse.set({
              left: Math.min(start.x, pointer.x),
              top: Math.min(start.y, pointer.y),
              rx: rx,
              ry: ry,
            });
          }

          canvas.renderAll();
        });

        canvas.on('mouse:up', () => {
          if (!isDrawingRef.current) return;

          isDrawingRef.current = false;

          // Add arrowhead for arrow tool
          if (tool === 'arrow' && activeShapeRef.current && startPointRef.current) {
            const line = activeShapeRef.current as fabric.Line;
            const x1 = startPointRef.current.x;
            const y1 = startPointRef.current.y;
            const x2 = line.x2 || x1;
            const y2 = line.y2 || y1;

            const angle = Math.atan2(y2 - y1, x2 - x1);
            const headLength = strokeWidth * 4;

            const arrowHead = new fabric.Triangle({
              left: x2,
              top: y2,
              width: headLength,
              height: headLength,
              fill: color,
              angle: (angle * 180 / Math.PI) + 90,
              originX: 'center',
              originY: 'center',
              selectable: false,
            });

            // Group line and arrowhead
            canvas.remove(line);
            const group = new fabric.Group([line, arrowHead], {
              selectable: false,
            });
            canvas.add(group);
            activeShapeRef.current = group;
          }

          saveHistory();
          startPointRef.current = null;
          activeShapeRef.current = null;
        });
      }
    }, [tool, color, strokeWidth, saveHistory]);

    // Update brush color/width when they change (for pencil tool)
    useEffect(() => {
      const canvas = fabricRef.current;
      if (!canvas || !canvas.isDrawingMode) return;

      if (canvas.freeDrawingBrush) {
        canvas.freeDrawingBrush.color = color;
        canvas.freeDrawingBrush.width = strokeWidth;
      }
    }, [color, strokeWidth]);

    // Expose methods via ref
    useImperativeHandle(ref, () => ({
      toDataURL: () => {
        if (!fabricRef.current) return '';
        return fabricRef.current.toDataURL({
          format: 'png',
          quality: 1,
          multiplier: 1,
        });
      },
      undo: () => {
        if (!fabricRef.current || historyIndexRef.current <= 0) return;
        historyIndexRef.current--;
        const json = historyRef.current[historyIndexRef.current];
        fabricRef.current.loadFromJSON(json).then(() => {
          fabricRef.current?.renderAll();
        });
      },
      redo: () => {
        if (!fabricRef.current || historyIndexRef.current >= historyRef.current.length - 1) return;
        historyIndexRef.current++;
        const json = historyRef.current[historyIndexRef.current];
        fabricRef.current.loadFromJSON(json).then(() => {
          fabricRef.current?.renderAll();
        });
      },
      canUndo: () => historyIndexRef.current > 0,
      canRedo: () => historyIndexRef.current < historyRef.current.length - 1,
      deleteSelected: () => {
        const canvas = fabricRef.current;
        if (!canvas) return;
        const activeObjects = canvas.getActiveObjects();
        if (activeObjects.length > 0) {
          activeObjects.forEach((obj) => canvas.remove(obj));
          canvas.discardActiveObject();
          canvas.renderAll();
          saveHistory();
        }
      },
    }));

    return (
      <div
        ref={containerRef}
        className="flex-1 flex items-center justify-center overflow-hidden bg-zinc-900 p-4"
        style={{ minHeight: '60vh' }}
      >
        <canvas ref={canvasRef} className="shadow-2xl" />
      </div>
    );
  }
);

ImageEditorCanvas.displayName = 'ImageEditorCanvas';

export default ImageEditorCanvas;
