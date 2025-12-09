"""
Project Manager for Save/Load/Export

Handles:
- Saving projects (.csp files)
- Loading projects
- Exporting images (.png)

"""

import pickle
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtGui import QPainter, QImage
from PyQt6.QtCore import Qt, QBuffer, QByteArray, QIODevice
from .layer import Layer


class ProjectManager:
    """Handles saving, loading, and exporting projects"""
    
    @staticmethod
    def save_project(parent, layers, width, height):
        """
        Save project to .csp file
        
        Args:
            parent: Parent widget for file dialog
            layers: List of Layer objects
            width: Canvas width
            height: Canvas height
        """
        filename, _ = QFileDialog.getSaveFileName(
            parent, 
            "Save Project", 
            "", 
            "Concept Studio Project (*.csp)"
        )
        
        if not filename:
            return  # User cancelled
        
        # Convert each layer to serializable format
        layer_data = []
        for layer in layers:
            # Convert QImage to bytes
            ba = QByteArray()
            buff = QBuffer(ba)
            buff.open(QIODevice.OpenModeFlag.WriteOnly)
            layer.image.save(buff, "PNG")  # Save as PNG in memory
            
            layer_data.append({
                "name": layer.name,
                "visible": layer.visible,
                "opacity": layer.opacity,
                "blend_mode": layer.blend_mode,
                "x": layer.x,
                "y": layer.y,
                "scale_x": layer.scale_x,
                "scale_y": layer.scale_y,
                "rotation": layer.rotation,
                "image_bytes": ba.data()  # PNG as bytes
            })
        
        # Create project state
        project_state = {
            "width": width,
            "height": height,
            "layers": layer_data,
            "version": "6.0"  # For future compatibility
        }
        
        # Save with pickle
        with open(filename, "wb") as f:
            pickle.dump(project_state, f)
        
        print(f"💾 Saved project: {filename}")
    
    @staticmethod
    def load_project(parent, canvas):
        """
        Load project from .csp file
        
        Args:
            parent: Parent widget for file dialog
            canvas: Canvas widget to load into
        """
        filename, _ = QFileDialog.getOpenFileName(
            parent, 
            "Open Project", 
            "", 
            "Concept Studio Project (*.csp)"
        )
        
        if not filename:
            return  # User cancelled
        
        try:
            # Load project state
            with open(filename, "rb") as f:
                project_state = pickle.load(f)
            
            # Reconstruct layers
            new_layers = []
            for l_data in project_state["layers"]:
                # Create new layer
                new_layer = Layer(
                    l_data["name"], 
                    project_state["width"], 
                    project_state["height"]
                )
                
                # Restore properties
                new_layer.visible = l_data["visible"]
                new_layer.opacity = l_data["opacity"]
                new_layer.blend_mode = l_data.get("blend_mode", "Normal")
                
                # Restore transform
                new_layer.x = l_data.get("x", 0.0)
                new_layer.y = l_data.get("y", 0.0)
                new_layer.scale_x = l_data.get("scale_x", 1.0)
                new_layer.scale_y = l_data.get("scale_y", 1.0)
                new_layer.rotation = l_data.get("rotation", 0.0)
                
                # Restore image from bytes
                loaded_image = QImage.fromData(l_data["image_bytes"])
                new_layer.image = loaded_image.convertToFormat(
                    QImage.Format.Format_ARGB32_Premultiplied
                )
                
                new_layers.append(new_layer)
            
            # Replace canvas layers
            canvas.layers = new_layers
            canvas.active_layer_index = len(new_layers) - 1
            canvas.history.undo_stack.clear()
            canvas.history.redo_stack.clear()
            canvas.update()
            
            print(f"✅ Loaded project: {filename}")
            print(f"   Layers: {len(new_layers)}")
            
        except Exception as e:
            print(f"❌ Error loading project: {e}")
    
    @staticmethod
    def export_image(parent, canvas):
        """
        Export flattened image as PNG
        
        Args:
            parent: Parent widget for file dialog
            canvas: Canvas widget to export from
        """
        filename, _ = QFileDialog.getSaveFileName(
            parent, 
            "Export PNG", 
            "", 
            "PNG Image (*.png)"
        )
        
        if not filename:
            return  # User cancelled
        
        # Create result image
        result = QImage(
            canvas.canvas_width, 
            canvas.canvas_height, 
            QImage.Format.Format_ARGB32_Premultiplied
        )
        result.fill(Qt.GlobalColor.transparent)
        
        # Composite all visible layers
        painter = QPainter(result)
        for layer in canvas.layers:
            if layer.visible:
                painter.setOpacity(layer.opacity)
                # Note: Transforms not applied in basic export
                # Add transform logic here for v7!
                painter.drawImage(0, 0, layer.image)
        painter.end()
        
        # Save
        result.save(filename)
        print(f"🖼️ Exported image: {filename}")
