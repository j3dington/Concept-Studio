"""
CONCEPT STUDIO - Desktop Art Application
Built with Python, CustomTkinter, and PIL/Pillow

A+ LEARNING NOTE:
This demonstrates GUI programming in Python:
- Event-driven programming (button clicks, mouse moves)
- Object-oriented design (Layer class, App class)
- Image processing with PIL
- Memory management concepts
"""

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk, ImageFilter
import math
from typing import List, Tuple
import io

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class Layer:
    """
    Represents a single drawing layer with its own image buffer.
    
    LEARNING NOTE: This is object-oriented programming (OOP)!
    Each layer is an "object" with its own data (image, name, opacity)
    and methods (clear, get_memory_size, etc.)
    """
    
    def __init__(self, name: str, width: int, height: int):
        self.name = name
        self.width = width
        self.height = height
        # PIL Image with RGBA (Red, Green, Blue, Alpha transparency)
        self.image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.visible = True
        self.opacity = 1.0
        self.id = id(self)  # Unique identifier
        
    def clear(self):
        """Clear the layer to transparent"""
        self.image = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
    def get_memory_size(self) -> float:
        """
        Calculate memory usage in MB
        
        A+ NOTE: Each pixel = 4 bytes (RGBA)
        1920x1080 = 2,073,600 pixels × 4 bytes = 8.3 MB per layer!
        """
        bytes_used = self.width * self.height * 4
        return bytes_used / (1024 * 1024)
    
    def copy(self):
        """Create a copy of this layer"""
        new_layer = Layer(f"{self.name} copy", self.width, self.height)
        new_layer.image = self.image.copy()
        new_layer.draw = ImageDraw.Draw(new_layer.image)
        new_layer.opacity = self.opacity
        return new_layer


class ConceptStudio(ctk.CTk):
    """
    Main application window
    
    LEARNING NOTE: This inherits from CTk (CustomTkinter window)
    Inheritance means we get all the window functionality for free!
    """
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Concept Studio - Desktop Art Application")
        self.geometry("1400x900")
        
        # Canvas settings
        self.canvas_width = 1200
        self.canvas_height = 800
        
        # Drawing state
        self.layers: List[Layer] = []
        self.active_layer_index = 0
        self.is_drawing = False
        self.last_x = 0
        self.last_y = 0
        
        # Tool settings
        self.current_tool = "brush"
        self.brush_size = 20
        self.brush_opacity = 100
        self.brush_hardness = 100
        self.brush_color = (0, 0, 0, 255)  # RGBA
        self.brush_spacing = 5
        
        # Memory tracking
        self.max_memory = 500  # MB
        
        # Create UI
        self.create_ui()
        
        # Create initial layer
        self.add_layer()
        
        # Composite and display
        self.composite_layers()
        
        print("🎨 Concept Studio initialized!")
        print(f"📚 Python + CustomTkinter + PIL")
        print(f"💾 Canvas: {self.canvas_width}x{self.canvas_height}")
        
    def create_ui(self):
        """Build the user interface"""
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ==================== TOP TOOLBAR ====================
        toolbar = ctk.CTkFrame(self, height=80, fg_color="#1a1a1a")
        toolbar.grid(row=0, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        toolbar.grid_columnconfigure(8, weight=1)
        
        # App title
        title = ctk.CTkLabel(
            toolbar,
            text="Concept Studio",
            font=("Helvetica", 20, "bold"),
            text_color="#357585"
        )
        title.grid(row=0, column=0, padx=20, pady=20)
        
        # Tool buttons
        self.brush_btn = ctk.CTkButton(
            toolbar,
            text="Brush (B)",
            width=100,
            command=lambda: self.set_tool("brush"),
            fg_color="#357585",
            hover_color="#2E4E57"
        )
        self.brush_btn.grid(row=0, column=1, padx=5, pady=20)
        
        self.eraser_btn = ctk.CTkButton(
            toolbar,
            text="Eraser (E)",
            width=100,
            command=lambda: self.set_tool("eraser"),
            fg_color="#4a4a4a",
            hover_color="#6a6a6a"
        )
        self.eraser_btn.grid(row=0, column=2, padx=5, pady=20)
        
        # Brush size
        ctk.CTkLabel(toolbar, text="Size:").grid(row=0, column=3, padx=(20, 5))
        self.size_slider = ctk.CTkSlider(
            toolbar,
            from_=1,
            to=100,
            width=150,
            command=self.on_size_change
        )
        self.size_slider.set(5)
        self.size_slider.grid(row=0, column=4, padx=5)
        
        self.size_label = ctk.CTkLabel(toolbar, text="5px", width=40)
        self.size_label.grid(row=0, column=5, padx=5)
        
        # Brush opacity
        ctk.CTkLabel(toolbar, text="Opacity:").grid(row=0, column=6, padx=(20, 5))
        self.opacity_slider = ctk.CTkSlider(
            toolbar,
            from_=0,
            to=100,
            width=150,
            command=self.on_opacity_change
        )
        self.opacity_slider.set(100)
        self.opacity_slider.grid(row=0, column=7, padx=5)
        
        self.opacity_label = ctk.CTkLabel(toolbar, text="100%", width=50)
        self.opacity_label.grid(row=0, column=8, padx=5, sticky="w")
        
        # Color picker button
        self.color_btn = ctk.CTkButton(
            toolbar,
            text="🎨",
            width=50,
            command=self.pick_color,
            fg_color="#000000"
        )
        self.color_btn.grid(row=0, column=9, padx=20)
        
        # Clear and Export
        ctk.CTkButton(
            toolbar,
            text="Clear",
            width=80,
            command=self.clear_layer,
            fg_color="#357585"
        ).grid(row=0, column=10, padx=5)
        
        ctk.CTkButton(
            toolbar,
            text="Export",
            width=80,
            command=self.export_image,
            fg_color="#357585"
        ).grid(row=0, column=11, padx=5)
        
        # ==================== LEFT PANEL ====================
        left_panel = ctk.CTkFrame(self, width=250, fg_color="#1a1a1a")
        left_panel.grid(row=1, column=0, sticky="ns", padx=0, pady=0)
        left_panel.grid_propagate(False)
        
        # Brush settings
        ctk.CTkLabel(
            left_panel,
            text="BRUSH SETTINGS",
            font=("Helvetica", 11, "bold"),
            text_color="#357585"
        ).pack(padx=20, pady=(20, 10))
        
        # Hardness
        ctk.CTkLabel(left_panel, text="Hardness:").pack(padx=20, pady=(10, 0))
        self.hardness_slider = ctk.CTkSlider(
            left_panel,
            from_=0,
            to=100,
            command=self.on_hardness_change
        )
        self.hardness_slider.set(100)
        self.hardness_slider.pack(padx=20, pady=5)
        
        # Spacing
        ctk.CTkLabel(left_panel, text="Spacing:").pack(padx=20, pady=(10, 0))
        self.spacing_slider = ctk.CTkSlider(
            left_panel,
            from_=1,
            to=50,
            command=self.on_spacing_change
        )
        self.spacing_slider.set(5)
        self.spacing_slider.pack(padx=20, pady=5)
        
        # Memory display
        ctk.CTkLabel(
            left_panel,
            text="MEMORY USAGE",
            font=("Helvetica", 11, "bold"),
            text_color="#357585"
        ).pack(padx=20, pady=(30, 10))
        
        self.memory_label = ctk.CTkLabel(
            left_panel,
            text="0.0 MB / 500 MB",
            font=("Courier", 12)
        )
        self.memory_label.pack(padx=20, pady=5)
        
        self.memory_bar = ctk.CTkProgressBar(left_panel, width=200)
        self.memory_bar.set(0)
        self.memory_bar.pack(padx=20, pady=5)
        
        ctk.CTkLabel(
            left_panel,
            text="Disk cache ready for\nlarge files",
            font=("Helvetica", 9),
            text_color="#6a6a6a"
        ).pack(padx=20, pady=5)
        
        # ==================== CANVAS AREA ====================
        canvas_container = ctk.CTkFrame(self, fg_color="#2a2a2a")
        canvas_container.grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        
        # Create canvas widget
        self.canvas = ctk.CTkCanvas(
            canvas_container,
            width=self.canvas_width,
            height=self.canvas_height,
            bg="#ffffff",
            highlightthickness=0,
            cursor="crosshair"
        )
        self.canvas.pack(expand=True)
        
        # Bind mouse events
        self.canvas.bind("<Button-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        
        # ==================== RIGHT PANEL ====================
        right_panel = ctk.CTkFrame(self, width=280, fg_color="#1a1a1a")
        right_panel.grid(row=1, column=2, sticky="ns", padx=0, pady=0)
        right_panel.grid_propagate(False)
        
        # Layers section
        ctk.CTkLabel(
            right_panel,
            text="LAYERS",
            font=("Helvetica", 11, "bold"),
            text_color="#b8995f"
        ).pack(padx=20, pady=(20, 10))
        
        # Layers list
        self.layers_frame = ctk.CTkScrollableFrame(
            right_panel,
            width=240,
            height=400,
            fg_color="#2a2a2a"
        )
        self.layers_frame.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Add layer button
        ctk.CTkButton(
            right_panel,
            text="+ New Layer",
            command=self.add_layer,
            fg_color="#4a4a4a",
            hover_color="#6a6a6a"
        ).pack(padx=20, pady=10)
        
        # Layer opacity
        ctk.CTkLabel(
            right_panel,
            text="LAYER PROPERTIES",
            font=("Helvetica", 11, "bold"),
            text_color="#b8995f"
        ).pack(padx=20, pady=(10, 5))
        
        ctk.CTkLabel(right_panel, text="Layer Opacity:").pack(padx=20, pady=(10, 0))
        self.layer_opacity_slider = ctk.CTkSlider(
            right_panel,
            from_=0,
            to=100,
            command=self.on_layer_opacity_change
        )
        self.layer_opacity_slider.set(100)
        self.layer_opacity_slider.pack(padx=20, pady=5)
        
        # ==================== STATUS BAR ====================
        status = ctk.CTkFrame(self, height=30, fg_color="#1a1a1a")
        status.grid(row=2, column=0, columnspan=3, sticky="ew", padx=0, pady=0)
        
        self.cursor_label = ctk.CTkLabel(
            status,
            text="Cursor: 0, 0",
            font=("Courier", 10)
        )
        self.cursor_label.pack(side="left", padx=20, pady=5)
        
        self.canvas_size_label = ctk.CTkLabel(
            status,
            text=f"Canvas: {self.canvas_width} x {self.canvas_height}",
            font=("Courier", 10)
        )
        self.canvas_size_label.pack(side="left", padx=20, pady=5)
        
        # Bind keyboard shortcuts
        self.bind("<KeyPress-b>", lambda e: self.set_tool("brush"))
        self.bind("<KeyPress-e>", lambda e: self.set_tool("eraser"))
        self.bind("<KeyPress-bracketleft>", lambda e: self.decrease_brush_size())
        self.bind("<KeyPress-bracketright>", lambda e: self.increase_brush_size())
        
    # ==================== TOOL MANAGEMENT ====================
    
    def set_tool(self, tool: str):
        """Switch between brush and eraser"""
        self.current_tool = tool
        if tool == "brush":
            self.brush_btn.configure(fg_color="#b8995f")
            self.eraser_btn.configure(fg_color="#4a4a4a")
        else:
            self.brush_btn.configure(fg_color="#4a4a4a")
            self.eraser_btn.configure(fg_color="#b8995f")
    
    def on_size_change(self, value):
        """Update brush size"""
        self.brush_size = int(value)
        self.size_label.configure(text=f"{self.brush_size}px")
    
    def on_opacity_change(self, value):
        """Update brush opacity"""
        self.brush_opacity = int(value)
        self.opacity_label.configure(text=f"{self.brush_opacity}%")
    
    def on_hardness_change(self, value):
        """Update brush hardness"""
        self.brush_hardness = int(value)
    
    def on_spacing_change(self, value):
        """Update brush spacing"""
        self.brush_spacing = int(value)
    
    def on_layer_opacity_change(self, value):
        """Update active layer opacity"""
        if self.layers:
            self.layers[self.active_layer_index].opacity = value / 100
            self.composite_layers()
    
    def decrease_brush_size(self):
        """Keyboard shortcut: ["""
        new_size = max(1, self.brush_size - 5)
        self.size_slider.set(new_size)
        self.on_size_change(new_size)
    
    def increase_brush_size(self):
        """Keyboard shortcut: ]"""
        new_size = min(100, self.brush_size + 5)
        self.size_slider.set(new_size)
        self.on_size_change(new_size)
    
    def pick_color(self):
        """Open color picker dialog"""
        from tkinter import colorchooser
        color = colorchooser.askcolor(title="Choose brush color")
        if color[0]:  # Returns ((R, G, B), "#RRGGBB")
            r, g, b = [int(c) for c in color[0]]
            self.brush_color = (r, g, b, 255)
            self.color_btn.configure(fg_color=color[1])
    
    # ==================== DRAWING ENGINE ====================
    
    def on_mouse_down(self, event):
        """Start drawing"""
        self.is_drawing = True
        self.last_x = event.x
        self.last_y = event.y
        self.draw_point(event.x, event.y)
    
    def on_mouse_drag(self, event):
        """Continue drawing"""
        if self.is_drawing:
            self.draw_line(self.last_x, self.last_y, event.x, event.y)
            self.last_x = event.x
            self.last_y = event.y
    
    def on_mouse_up(self, event):
        """Stop drawing"""
        self.is_drawing = False
        self.composite_layers()
        self.update_memory_display()
    
    def on_mouse_move(self, event):
        """Update cursor position"""
        self.cursor_label.configure(text=f"Cursor: {event.x}, {event.y}")
    
    def draw_point(self, x: int, y: int):
        """
        Draw a single brush stroke at point (x, y)
        
        LEARNING NOTE: This creates a soft brush using PIL's ellipse drawing
        with alpha transparency for opacity
        """
        if not self.layers:
            return
        
        layer = self.layers[self.active_layer_index]
        size = self.brush_size
        opacity = int((self.brush_opacity / 100) * 255)
        
        if self.current_tool == "eraser":
            # Eraser: draw transparent
            color = (0, 0, 0, 0)
            # For eraser, we need to use a different approach
            temp_img = Image.new('RGBA', layer.image.size, (0, 0, 0, 0))
            temp_draw = ImageDraw.Draw(temp_img)
            temp_draw.ellipse(
                [x - size//2, y - size//2, x + size//2, y + size//2],
                fill=(255, 255, 255, opacity)
            )
            # Composite with destination-out effect
            layer.image.paste((0, 0, 0, 0), (0, 0), temp_img)
        else:
            # Brush: draw with color
            r, g, b, _ = self.brush_color
            color = (r, g, b, opacity)
            
            # Create soft brush if hardness < 100
            if self.brush_hardness < 100:
                # Create a brush stamp with gradient
                brush_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
                brush_draw = ImageDraw.Draw(brush_img)
                
                # Draw gradient circles for soft edge
                for i in range(size // 2):
                    alpha = int(opacity * (1 - (i / (size // 2)) * (1 - self.brush_hardness / 100)))
                    brush_draw.ellipse(
                        [i, i, size - i, size - i],
                        fill=(r, g, b, alpha)
                    )
                
                # Paste the brush stamp
                layer.image.paste(brush_img, (x - size//2, y - size//2), brush_img)
            else:
                # Hard brush
                layer.draw.ellipse(
                    [x - size//2, y - size//2, x + size//2, y + size//2],
                    fill=color
                )
        
        # Update display
        self.composite_layers()
    
    def draw_line(self, x1: int, y1: int, x2: int, y2: int):
        """
        Draw a smooth line between two points
        
        LEARNING NOTE: We interpolate points to avoid gaps in the line.
        This is essential for smooth brush strokes!
        """
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Calculate number of points based on spacing
        num_points = max(1, int(distance / self.brush_spacing))
        
        # Draw points along the line
        for i in range(num_points + 1):
            t = i / max(num_points, 1)
            x = int(x1 + dx * t)
            y = int(y1 + dy * t)
            self.draw_point(x, y)
    
    # ==================== LAYER MANAGEMENT ====================
    
    def add_layer(self):
        """Create a new layer"""
        layer_num = len(self.layers) + 1
        layer = Layer(f"Layer {layer_num}", self.canvas_width, self.canvas_height)
        self.layers.append(layer)
        self.active_layer_index = len(self.layers) - 1
        
        self.update_layers_list()
        self.update_memory_display()
        print(f"✅ Created: {layer.name} ({layer.get_memory_size():.1f} MB)")
    
    def update_layers_list(self):
        """Refresh the layers panel"""
        # Clear existing widgets
        for widget in self.layers_frame.winfo_children():
            widget.destroy()
        
        # Create layer buttons (reverse order, top to bottom)
        for i in range(len(self.layers) - 1, -1, -1):
            layer = self.layers[i]
            is_active = (i == self.active_layer_index)
            
            frame = ctk.CTkFrame(
                self.layers_frame,
                fg_color="#b8995f" if is_active else "#4a4a4a",
                height=60
            )
            frame.pack(fill="x", pady=5)
            frame.pack_propagate(False)
            
            btn = ctk.CTkButton(
                frame,
                text=f"{layer.name}\nOpacity: {int(layer.opacity * 100)}%",
                command=lambda idx=i: self.set_active_layer(idx),
                fg_color="transparent",
                hover_color="#6a6a6a",
                anchor="w"
            )
            btn.pack(fill="both", expand=True, padx=5, pady=5)
    
    def set_active_layer(self, index: int):
        """Switch to a different layer"""
        self.active_layer_index = index
        self.update_layers_list()
        
        layer = self.layers[index]
        self.layer_opacity_slider.set(int(layer.opacity * 100))
    
    def composite_layers(self):
        """
        Combine all layers into final image and display
        
        LEARNING NOTE: This is how Photoshop works!
        Each layer is composited onto a white background in order.
        """
        # Create white background
        result = Image.new('RGB', (self.canvas_width, self.canvas_height), (255, 255, 255))
        
        # Composite each visible layer
        for layer in self.layers:
            if layer.visible:
                # Apply layer opacity
                if layer.opacity < 1.0:
                    temp = layer.image.copy()
                    alpha = temp.split()[3]
                    alpha = alpha.point(lambda p: int(p * layer.opacity))
                    temp.putalpha(alpha)
                    result.paste(temp, (0, 0), temp)
                else:
                    result.paste(layer.image, (0, 0), layer.image)
        
        # Display on canvas
        self.display_image = ImageTk.PhotoImage(result)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.display_image)
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def update_memory_display(self):
        """
        Calculate and display memory usage
        
        A+ NOTE: Real apps monitor RAM usage and write to disk when needed.
        This simulates that concept!
        """
        total_memory = sum(layer.get_memory_size() for layer in self.layers)
        memory_percent = (total_memory / self.max_memory)
        
        self.memory_label.configure(text=f"{total_memory:.1f} MB / {self.max_memory} MB")
        self.memory_bar.set(min(1.0, memory_percent))
        
        if total_memory > self.max_memory * 0.8:
            print("⚠️ High memory usage! Would write to scratch disk in production.")
    
    def clear_layer(self):
        """Clear the active layer"""
        if self.layers:
            self.layers[self.active_layer_index].clear()
            self.composite_layers()
            print(f"🗑️ Cleared {self.layers[self.active_layer_index].name}")
    
    def export_image(self):
        """Export the composited image as PNG"""
        from tkinter import filedialog
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filepath:
            # Composite all layers
            result = Image.new('RGB', (self.canvas_width, self.canvas_height), (255, 255, 255))
            for layer in self.layers:
                if layer.visible:
                    if layer.opacity < 1.0:
                        temp = layer.image.copy()
                        alpha = temp.split()[3]
                        alpha = alpha.point(lambda p: int(p * layer.opacity))
                        temp.putalpha(alpha)
                        result.paste(temp, (0, 0), temp)
                    else:
                        result.paste(layer.image, (0, 0), layer.image)
            
            result.save(filepath, 'PNG')
            print(f"💾 Saved: {filepath}")


def main():
    """
    Entry point for the application
    
    LEARNING NOTE: This is the main() function - where Python programs start!
    """
    print("""
╔══════════════════════════════════════════════════════════════╗
║             CONCEPT STUDIO - Desktop Edition                  ║
║                   Python + CustomTkinter                      ║
╚══════════════════════════════════════════════════════════════╝

🎨 FEATURES:
   • Smooth brush engine with opacity and hardness
   • Multi-layer system
   • Memory management simulation
   • Keyboard shortcuts (B=Brush, E=Eraser, [/]=Size)

📚 LEARNING CONCEPTS:
   • GUI programming with CustomTkinter
   • Image processing with PIL/Pillow
   • Event-driven programming
   • Object-oriented design

🔧 A+ CERTIFICATION NOTES:
   • Memory = RAM (fast, volatile)
   • Disk = Storage (slower, persistent)
   • Apps use scratch disk when RAM fills up
   • Each 1920x1080 layer = ~8.3 MB RAM

Ready to draw! 🖌️
    """)
    
    app = ConceptStudio()
    app.mainloop()


if __name__ == "__main__":
    main()
