"""
Create a simple icon for OpenSuperWhisper
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_icon():
    """Create a simple icon for the application"""
    
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a circle background
    margin = 20
    draw.ellipse(
        [margin, margin, size-margin, size-margin],
        fill='#1a1a1a',
        outline='#333333',
        width=3
    )
    
    # Draw a microphone shape
    mic_width = 60
    mic_height = 100
    mic_x = (size - mic_width) // 2
    mic_y = (size - mic_height) // 2 - 20
    
    # Microphone body
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        radius=mic_width//2,
        fill='#ef4444',
        outline='#dc2626',
        width=2
    )
    
    # Microphone stand
    stand_width = 80
    stand_x = (size - stand_width) // 2
    stand_y = mic_y + mic_height - 10
    
    # Stand arc
    draw.arc(
        [stand_x, stand_y, stand_x + stand_width, stand_y + 40],
        start=0,
        end=180,
        fill='#666666',
        width=4
    )
    
    # Stand base
    base_width = 40
    base_x = (size - base_width) // 2
    base_y = stand_y + 40
    
    draw.line(
        [(size//2, base_y), (size//2, base_y + 20)],
        fill='#666666',
        width=4
    )
    
    draw.line(
        [base_x, base_y + 20, base_x + base_width, base_y + 20],
        fill='#666666',
        width=4
    )
    
    # Add some detail to the microphone
    for i in range(3):
        y = mic_y + 20 + i * 20
        draw.line(
            [mic_x + 10, y, mic_x + mic_width - 10, y],
            fill='#b91c1c',
            width=2
        )
    
    # Save as ICO file with multiple sizes
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    
    # Create a list of images for the ICO file
    images = []
    for size in icon_sizes:
        resized = img.resize(size, Image.Resampling.LANCZOS)
        images.append(resized)
    
    # Save as ICO
    images[0].save(
        'opensuperwhisper.ico',
        format='ICO',
        sizes=icon_sizes,
        append_images=images[1:]
    )
    
    # Also save as PNG for other uses
    img.save('opensuperwhisper.png', 'PNG')
    
    print("Icon created successfully!")


if __name__ == "__main__":
    try:
        create_icon()
    except Exception as e:
        print(f"Failed to create icon: {e}")
        print("You'll need to create an icon manually or use a placeholder")