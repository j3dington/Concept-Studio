import zipfile
import json
import os
import shutil
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
from PyQt6.QtGui import QImage, QPainter

class ProjectManager:
    @staticmethod
    def save_project(parent, layers, width, height):
        # === Ask where to save === #
        filename, _ = QFileDialog.getSaveFileName(parent, "Save Project", "", "Concept Studio Project (*.csp)")
        if not filename: return
            
        print(f"💾 Saving to {filename}...")
        
        # === Create a Temporary Folder Structure === #
        temp_dir = "temp_save_data"
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
        
        # === Save Layers as PNGs === #
        layer_info = []
        
        try:
            for i, layer in enumerate(layers):
                # === Save the Image Data === #
                image_name = f"layer_{i}.png"
                image_path = os.path.join(temp_dir, image_name)
                layer.image.save(image_path, "PNG")
                
                # === Record the Metadata === #
                layer_info.append({
                    "name": layer.name,
                    "filename": image_name,
                    "visible": layer.visible,
                    "opacity": layer.opacity,
                    "blend_mode": layer.blend_mode,
                    "is_floating": getattr(layer, "is_floating", False),
                    # Transform Props
                    "x": getattr(layer, "x", 0),
                    "y": getattr(layer, "y", 0),
                    "rotation": getattr(layer, "rotation", 0),
                    "scale_x": getattr(layer, "scale_x", 1),
                    "scale_y": getattr(layer, "scale_y", 1)
                })
                
            # === Save the "Stack" (Metadata) as JSON === #
            project_data = {
                "width": width,
                "height": height,
                "layers": layer_info
            }
            
            with open(os.path.join(temp_dir, "stack.json"), "w") as f:
                json.dump(project_data, f, indent=4)
                
            # === Zip it all up! === #
            with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Add file to zip, but remove the 'temp_save_data' prefix
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
                        
            print("✅ Save Complete!")
            
        except Exception as e:
            print(f"❌ Save Failed: {e}")
        finally:
            # === Cleanup Temp Files === #
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)

    @staticmethod
    def load_project(parent, canvas):
        from ui.canvas import Layer 
        
        filename, _ = QFileDialog.getOpenFileName(parent, "Open Project", "", "Concept Studio Project (*.csp)")
        if not filename: return
        
        print(f"📂 Loading {filename}...")
        
        temp_dir = "temp_load_data"
        if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        
        try:
            # === Unzip === #
            with zipfile.ZipFile(filename, 'r') as zipf:
                zipf.extractall(temp_dir)
                
            # === Read Metadata === #
            with open(os.path.join(temp_dir, "stack.json"), "r") as f:
                project_data = json.load(f)
            
            # === Reconstruct Layers === #
            new_layers = []
            width = project_data["width"]
            height = project_data["height"]
            
            # === Update Canvas Dimensions if Needed (v2 Feature) === #
            canvas.canvas_width = width
            canvas.canvas_height = height
            
            for l_data in project_data["layers"]:
                # === Create Blank Layer === #
                new_layer = Layer(l_data["name"], width, height)
                
                # === Restore Properties === #
                new_layer.visible = l_data["visible"]
                new_layer.opacity = l_data["opacity"]
                new_layer.blend_mode = l_data.get("blend_mode", "Normal")
                new_layer.is_floating = l_data.get("is_floating", False)
                
                new_layer.x = l_data.get("x", 0)
                new_layer.y = l_data.get("y", 0)
                new_layer.rotation = l_data.get("rotation", 0)
                new_layer.scale_x = l_data.get("scale_x", 1)
                new_layer.scale_y = l_data.get("scale_y", 1)
                
                # === Load Image Data === #
                image_path = os.path.join(temp_dir, l_data["filename"])
                if os.path.exists(image_path):
                    loaded_image = QImage(image_path)
                    # Convert ensures format compatibility
                    new_layer.image = loaded_image.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                
                new_layers.append(new_layer)
            
            # === Apply to Canvas === #
            canvas.layers = new_layers
            canvas.active_layer_index = len(new_layers) - 1
            canvas.history.undo_stack.clear()
            canvas.update()
            print("✅ Load Complete!")
            
        except Exception as e:
            print(f"❌ Load Failed: {e}")
        finally:
            if os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            
    @staticmethod
    def export_image(parent, canvas):
        filename, _ = QFileDialog.getSaveFileName(parent, "Export PNG", "", "PNG Image (*.png)")
        if not filename: return
        
        # === Create a buffer for the final image === #
        result = QImage(canvas.canvas_width, canvas.canvas_height, QImage.Format.Format_ARGB32_Premultiplied)
        result.fill(0) # Transparent
        
        painter = QPainter(result)
        from PyQt6.QtGui import QTransform
        
        for layer in canvas.layers:
            if layer.visible:
                painter.setOpacity(layer.opacity)
                
                # Apply the same matrix math as the canvas
                t = QTransform()
                t.translate(layer.x, layer.y)
                cx, cy = layer.image.width()/2, layer.image.height()/2
                t.translate(cx, cy); t.rotate(layer.rotation); t.scale(layer.scale_x, layer.scale_y); t.translate(-cx, -cy)
                
                painter.setTransform(t)
                painter.drawImage(0, 0, layer.image)
                # Reset transform for next layer
                painter.resetTransform()
                
        painter.end()
        result.save(filename)