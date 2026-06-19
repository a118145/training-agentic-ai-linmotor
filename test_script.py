import linmotor as lm
from linmotor.visualize import plot_motor, plot_thrust_curve


m = lm.example_motor(halbach=True)

print("Konsistenz:", m.consistency_issues() or "OK")
disp = 4.0
#off = lm.find_commutation_offset(m)                 # einmalig nach Aufbau
off = 0.0
print(f"Offset = {off:.3f}rad ({off*180/3.14159:.1f}°)") 
f = lm.force(m, displacement_mm=disp, theta_offset=off)
print(f"F = ({f.fx:.2f}, {f.fz:.2f}) N, |F| = {f.magnitude:.2f} N")
xs = [k for k in range(int(2 * m.track.pole_pitch_mm))]
# samples = lm.thrust_curve(m, xs, theta_offset=off)
print(f"xs: {xs}")
# print(f"Samples: {samples}")

plot_motor(m, "motor.png", displacement_mm=disp, theta_offset=off)
plot_thrust_curve(m, "thrust_curve.png", theta_offset=off)
