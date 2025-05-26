"""
Create banner images for Inno Setup installer
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_installer_banner():
    """Create installer banner image (164x314 pixels)"""
    width, height = 164, 314
    img = Image.new('RGB', (width, height), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Draw a gradient-like background
    for y in range(height):
        color_value = int(26 + (y / height) * 20)
        draw.line([(0, y), (width, y)], fill=(color_value, color_value, color_value))
    
    # Draw microphone icon
    mic_size = 60
    mic_x = (width - mic_size) // 2
    mic_y = height // 2 - 50
    
    # Microphone body
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_size, mic_y + mic_size * 1.5],
        radius=mic_size//2,
        fill='#ef4444',
        outline='#dc2626',
        width=2
    )
    
    # Add text
    try:
        # Try to use a nice font, fallback to default if not available
        font = ImageFont.truetype("arial.ttf", 16)
        small_font = ImageFont.truetype("arial.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # App name
    text = "OpenSuperWhisper"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) // 2, mic_y + mic_size * 1.5 + 20),
        text,
        fill='#ffffff',
        font=font
    )
    
    # Tagline
    tagline = "Speech Transcription"
    bbox = draw.textbbox((0, 0), tagline, font=small_font)
    text_width = bbox[2] - bbox[0]
    draw.text(
        ((width - text_width) // 2, mic_y + mic_size * 1.5 + 45),
        tagline,
        fill='#cccccc',
        font=small_font
    )
    
    # Save as BMP
    img.save('installer_banner.bmp', 'BMP')
    print("Created installer_banner.bmp")


def create_installer_small_image():
    """Create small installer image (55x55 pixels)"""
    size = 55
    img = Image.new('RGB', (size, size), color='#1a1a1a')
    draw = ImageDraw.Draw(img)
    
    # Draw a circle background
    margin = 5
    draw.ellipse(
        [margin, margin, size-margin, size-margin],
        fill='#2a2a2a',
        outline='#404040',
        width=1
    )
    
    # Draw a simple microphone
    mic_width = 16
    mic_height = 24
    mic_x = (size - mic_width) // 2
    mic_y = (size - mic_height) // 2 - 3
    
    # Microphone body
    draw.rounded_rectangle(
        [mic_x, mic_y, mic_x + mic_width, mic_y + mic_height],
        radius=mic_width//2,
        fill='#ef4444'
    )
    
    # Stand
    stand_width = 20
    stand_x = (size - stand_width) // 2
    stand_y = mic_y + mic_height - 2
    
    draw.arc(
        [stand_x, stand_y, stand_x + stand_width, stand_y + 10],
        start=0,
        end=180,
        fill='#666666',
        width=2
    )
    
    # Save as BMP
    img.save('installer_small.bmp', 'BMP')
    print("Created installer_small.bmp")


def main():
    """Create all installer images"""
    try:
        print("Creating installer images...")
        create_installer_banner()
        create_installer_small_image()
        print("All installer images created successfully!")
    except Exception as e:
        print(f"Error creating images: {e}")
        print("Creating placeholder images...")
        
        # Create minimal placeholder images if PIL fails
        # Banner (164x314)
        with open('installer_banner.bmp', 'wb') as f:
            # Minimal BMP header + black image
            f.write(b'BM')  # Signature
            f.write(b'\x00' * 164 * 314 * 3)  # Placeholder
            
        # Small (55x55)
        with open('installer_small.bmp', 'wb') as f:
            # Minimal BMP header + black image
            f.write(b'BM')  # Signature
            f.write(b'\x00' * 55 * 55 * 3)  # Placeholder
            
        print("Created placeholder BMP files")


if __name__ == "__main__":
    main()