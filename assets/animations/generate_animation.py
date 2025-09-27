import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# Setup figure and axis
fig, ax = plt.subplots(figsize=(8, 6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 10)
ax.set_axis_off()
ax.set_title("Excel Monument Revival")

# Monument: a simple rectangle pillar with "Excel" text
monument = plt.Rectangle((4, 1), 2, 6, fc='green', ec='black')
ax.add_patch(monument)
text = ax.text(5, 4, "Excel", ha='center', va='center', fontsize=20, color='white')

# Snow: random white dots on monument
snow_particles = np.random.uniform(4, 6, 50), np.random.uniform(1, 7, 50)
snow = ax.scatter(*snow_particles, c='white', s=10)

# Youngsters: fast-moving red dots zipping around
youngsters_x = np.random.uniform(0, 10, 10)
youngsters_y = np.random.uniform(0, 10, 10)
youngsters = ax.scatter(youngsters_x, youngsters_y, c='red', s=20)

# Animation parameters
frames = 150
shake_start = 50
dance_start = 80
flip_start = 110
settle_start = 130

def animate(frame):
    global youngsters_x, youngsters_y
    # Youngsters always zipping
    youngsters_x = (youngsters_x + np.random.uniform(-0.5, 0.5, 10)) % 10
    youngsters_y = (youngsters_y + np.random.uniform(-0.5, 0.5, 10)) % 10
    youngsters.set_offsets(np.c_[youngsters_x, youngsters_y])
    
    # Snow coverage until shake
    if frame < shake_start:
        pass  # Snow stays
    elif shake_start <= frame < dance_start:
        # Shake off snow: move particles down and fade
        snow_y = snow_particles[1] - (frame - shake_start) * 0.1
        snow.set_offsets(np.c_[snow_particles[0], snow_y])
        snow.set_alpha(1 - (frame - shake_start) / (dance_start - shake_start))
    
    # Dance moves: wiggle monument
    if dance_start <= frame < flip_start:
        wiggle = np.sin((frame - dance_start) * 0.5) * 0.2
        monument.set_xy((4 + wiggle, 1))
        text.set_position((5 + wiggle, 4))
    
    # Backflip: rotate monument
    if flip_start <= frame < settle_start:
        angle = (frame - flip_start) * 18  # 360 degrees over 20 frames
        # Simple rotation simulation (Matplotlib patches don't rotate easily; approximate with resize/reposition)
        height = 6 * np.abs(np.cos(np.deg2rad(angle)))
        y_offset = 1 + (6 - height) / 2
        monument.set_height(height)
        monument.set_y(y_offset)
    
    # Settle back
    if frame >= settle_start:
        monument.set_xy((4, 1))
        monument.set_height(6)
        text.set_position((5, 4))
    
    return monument, text, snow, youngsters

ani = animation.FuncAnimation(fig, animate, frames=frames, interval=50, blit=True)

# Save as MP4 (requires FFmpeg) or GIF
# ani.save('excel_monument.mp4', writer='ffmpeg', fps=30)
ani.save('excel_monument.gif', writer='pillow', fps=30)  # GIF alternative, no FFmpeg needed

plt.show()  # Optional: preview in plot window
