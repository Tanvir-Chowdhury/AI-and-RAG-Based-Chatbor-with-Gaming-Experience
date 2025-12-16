import { useFrame, useThree } from "@react-three/fiber";
import { RigidBody, RapierRigidBody, CuboidCollider, CapsuleCollider, CylinderCollider, BallCollider, useRevoluteJoint } from "@react-three/rapier";
import { useRef, useMemo } from "react";
import { OrbitControls, useKeyboardControls } from "@react-three/drei";
import { Rover } from "./rover.jsx";
import { BoxGeometry, Quaternion, Vector3 } from "three";

function RoverController({ ref }: { ref: React.RefObject<RapierRigidBody | null> }) {
    const frameCount = useRef(0);
    const wheelUpdateInterval = 2; // Reduce frequency further

    const [, getKeys] = useKeyboardControls();
    const orbitRef = useRef<any>(null);

    const fl = useRef<any>(null);
    const fr = useRef<any>(null);
    const ml = useRef<any>(null);
    const mr = useRef<any>(null);
    const rl = useRef<any>(null);
    const rr = useRef<any>(null);
    const arm1 = useRef<any>(null);
    const arm2 = useRef<any>(null);
    const arm3 = useRef<any>(null);
    const arm4 = useRef<any>(null);
    const arm5 = useRef<any>(null);
    const sus_fl = useRef<any>(null);
    const sus_fr = useRef<any>(null);
    const sus_rl = useRef<any>(null);
    const sus_rr = useRef<any>(null);

    // Pre-allocate vectors to avoid garbage collection
    const wheelWorldPosition = useMemo(() => new Vector3(), []);
    const pointVelocity = useMemo(() => new Vector3(), []);
    const forward = useMemo(() => new Vector3(), []);
    const chassis_t = useMemo(() => new Vector3(), []);
    const chassis_r = useMemo(() => new Quaternion(), []);
    const relPoint = useMemo(() => new Vector3(), []);
    const angularVel = useMemo(() => new Vector3(), []);
    const linearVel = useMemo(() => new Vector3(), []);
    const angVelCrossRel = useMemo(() => new Vector3(), []);

    // Memoize wheel refs array
    const wheelRefs = useMemo(() => [fl, fr, ml, mr, rl, rr], []);

    // Constants
    const factor = 15;
    const moveSpeed = 60 * factor;
    const rotSpeed = 10 * factor;
    const wheelRadius = 0.2625;
    const lerpSpeed = 0.1;
    const steerSpeed = 0.06;

    function lerp(start: number, end: number, alpha: number) {
        return start + (end - start) * alpha;
    }

    // Optimized steering function
    const updateSteering = (susRefs: any[], targetAngles: number[], speeds: number[]) => {
        susRefs.forEach((susRef, index) => {
            if (susRef.current) {
                susRef.current.rotation.y = lerp(
                    susRef.current.rotation.y, 
                    targetAngles[index], 
                    speeds[index]
                );
            }
        });
    };

    useFrame((_, delta: number) => {
        if (!ref.current) return;
        
        const body = ref.current;
        const keys = getKeys();
        const { ArrowUp, ArrowDown, ArrowLeft, ArrowRight, w, a, s, d, q, e, i, k, j, l } = keys;

        // Get body transform once
        const t = body.translation();
        const r = body.rotation();
        chassis_t.set(t.x, t.y, t.z);
        chassis_r.set(r.x, r.y, r.z, r.w);

        // Calculate forward vector
        forward.set(0, 0, 1).applyQuaternion(chassis_r);

        // Movement logic
        const impulse = { x: 0, y: 0, z: 0 };
        if (ArrowUp || ArrowDown) {
            const direction = ArrowUp ? 1 : -1;
            impulse.x += forward.x * moveSpeed * direction;
            impulse.z += forward.z * moveSpeed * direction;

            // Only apply impulse if there's movement
            if (impulse.x !== 0 || impulse.z !== 0) {
                body.applyImpulse(impulse, true);
            }

            // Steering while moving
            if (ArrowLeft) {
                updateSteering(
                    [sus_fl, sus_fr, sus_rl, sus_rr],
                    [Math.PI / 5, Math.PI / 8, -Math.PI / 5, -Math.PI / 8],
                    [steerSpeed, steerSpeed * 0.5, steerSpeed, steerSpeed * 0.5]
                );
                body.applyTorqueImpulse({ x: 0, y: rotSpeed * (ArrowDown ? -1 : 1), z: 0 }, true);
            } else if (ArrowRight) {
                updateSteering(
                    [sus_fl, sus_fr, sus_rl, sus_rr],
                    [-Math.PI / 8, -Math.PI / 5, Math.PI / 8, Math.PI / 5],
                    [steerSpeed * 0.5, steerSpeed, steerSpeed * 0.5, steerSpeed]
                );
                body.applyTorqueImpulse({ x: 0, y: -rotSpeed * (ArrowDown ? -1 : 1), z: 0 }, true);
            } else {
                // Return to center when not steering
                updateSteering(
                    [sus_fl, sus_fr, sus_rl, sus_rr],
                    [0, 0, 0, 0],
                    [lerpSpeed, lerpSpeed, lerpSpeed, lerpSpeed]
                );
            }
        }

        // Tank steering (in place rotation)
        if ((ArrowLeft || ArrowRight) && !ArrowUp && !ArrowDown) {
            const direction = ArrowLeft ? 1 : -1;
            const maxAngle = Math.PI / 4;
            
            // Gradual wheel turning for tank steering
            updateSteering(
                [sus_fl, sus_fr, sus_rl, sus_rr],
                [-maxAngle, maxAngle, maxAngle, -maxAngle],
                [0.01, 0.01, 0.01, 0.01]
            );

            // Apply torque when wheels are positioned
            const avgAngle = (Math.abs(sus_fl.current?.rotation.y || 0) + 
                            Math.abs(sus_fr.current?.rotation.y || 0)) / 2;
            if (avgAngle > maxAngle * 0.8) {
                body.applyTorqueImpulse({ x: 0, y: rotSpeed * direction * 1.5, z: 0 }, true);
            }
        }

        // Arm controls (simplified to reduce frame load)
        frameCount.current++;
        if (frameCount.current % 2 === 0) { // Update arms every 2nd frame
            if (w && arm2.current?.rotation.z > -Math.PI / 2) {
                arm2.current.rotation.z -= 0.02;
            }
            if (s && arm2.current?.rotation.z < Math.PI / 2) {
                arm2.current.rotation.z += 0.02;
            }
            if (i && arm3.current) {
                arm3.current.rotation.z -= 0.02;
            }
            if (k && arm3.current) {
                arm3.current.rotation.z += 0.02;
            }
            if (a && arm1.current?.rotation.y < 0) {
                arm1.current.rotation.y += 0.02;
            }
            if (d && arm1.current?.rotation.y > -3.14) {
                arm1.current.rotation.y -= 0.02;
            }
            if (j && arm4.current?.rotation.z < 3.14) {
                arm4.current.rotation.z += 0.02;
            }
            if (l && arm4.current?.rotation.z > -1.0) {
                arm4.current.rotation.z -= 0.02;
            }
            if (q && arm5.current) {
                arm5.current.rotation.y += 0.02;
            }
            if (e && arm5.current) {
                arm5.current.rotation.y -= 0.02;
            }
        }

        // Update orbit controls
        if (orbitRef.current) {
            orbitRef.current.target.set(t.x, t.y + 1, t.z);
        }

        // Wheel rotation calculations (less frequent)
        if (frameCount.current % wheelUpdateInterval === 0) {
            const lv = body.linvel();
            const av = body.angvel();
            const center = body.translation();

            // Reuse vectors
            angularVel.set(av.x, av.y, av.z);
            linearVel.set(lv.x, lv.y, lv.z);

            wheelRefs.forEach((wheelRef) => {
                if (!wheelRef.current) return;

                wheelRef.current.getWorldPosition(wheelWorldPosition);

                relPoint.set(
                    wheelWorldPosition.x - center.x,
                    wheelWorldPosition.y - center.y,
                    wheelWorldPosition.z - center.z
                );

                angVelCrossRel.copy(angularVel).cross(relPoint);
                pointVelocity.copy(linearVel).add(angVelCrossRel);

                const signedSpeed = pointVelocity.dot(forward);
                const wheelRotation = (signedSpeed * delta) / wheelRadius;

                wheelRef.current.rotation.x += wheelRotation;
            });
        }

        // Reset frame counter periodically
        if (frameCount.current > 1000) {
            frameCount.current = 0;
        }
    });

    return (
        <>
            <RigidBody
                ref={ref}
                colliders={false}
                friction={0}
                linearDamping={10}
                angularDamping={10}
                position={[0, 3.8, 0]}
                rotation={[0, 0, 0]}
            >
                <Rover 
                    fl={fl} fr={fr} ml={ml} mr={mr} rl={rl} rr={rr} 
                    arm1={arm1} arm2={arm2} arm3={arm3} arm4={arm4} arm5={arm5} 
                    sus_fl={sus_fl} sus_fr={sus_fr} sus_rl={sus_rl} sus_rr={sus_rr} 
                />
                
                <CuboidCollider args={[.7, 0.4, 1.1]} position={[0, 1.1, -0.3]} mass={1000} />
                <CuboidCollider args={[.1, 0.1, .8]} position={[.3, .8, 1.5]} />

                <BallCollider args={[0.3]} position={[-1.05, 0.3, 1.1]} />
                <BallCollider args={[0.3]} position={[1.05, 0.3, 1.1]} />
                <BallCollider args={[0.3]} position={[-1.15, 0.3, -0.1]} />
                <BallCollider args={[0.3]} position={[1.15, 0.3, -0.1]} />
                <BallCollider args={[0.3]} position={[-1.05, 0.3, -1.2]} />
                <BallCollider args={[0.3]} position={[1.05, 0.3, -1.2]} />

                <OrbitControls
                    ref={orbitRef}
                    enablePan={false}
                    minDistance={3}
                    maxDistance={5}
                    maxPolarAngle={Math.PI / 1.9}
                />
            </RigidBody>
        </>
    );
}

export default RoverController;