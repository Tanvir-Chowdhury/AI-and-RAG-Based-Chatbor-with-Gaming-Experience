"use client";

import { Canvas, useFrame } from "@react-three/fiber";
import { KeyboardControls, Text3D } from "@react-three/drei";
import { Physics, RapierRigidBody, RigidBody } from "@react-three/rapier";
import { Mars } from "@/components/mars.jsx"

import RoverController from "@/components/roverController";
import { useMemo, useRef, useState } from "react";
import { DirectionalLight, Vector3 } from "three";
import { Crosshair, MapPin, MoveDown, MoveLeft, MoveRight, MoveUp, Pointer, PointerIcon } from "lucide-react";
import { ChatBar } from "@/components/sidebar";
import Info from "@/components/info";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";


// Add target position
let targetPosition = { x: 88, y: 0, z: -32 };
// const targetPosition = { x: 0, y: 0, z: 0 };


function Ground() {

  return (
    <RigidBody type="fixed" colliders={"trimesh"} position={[0, -275, 0]} rotation={[0, Math.PI, 0]}>
      <Mars />
    </RigidBody>
  );
}



function SunLight({ targetRef }: { targetRef: any }) {
  const lightRef = useRef<DirectionalLight>(null);

  useFrame(() => {
    if (lightRef.current && targetRef.current) {
      const roverPos = targetRef.current.translation();
      const lightPos = new Vector3(
        roverPos.x - 10,
        roverPos.y + 15,
        roverPos.z - 7
      );

      lightRef.current.position.copy(lightPos);
      lightRef.current.target.position.copy(roverPos);
      lightRef.current.target.updateMatrixWorld();
    }
  });

  return (
    <>
      <directionalLight
        ref={lightRef}
        intensity={2}
        castShadow
        shadow-mapSize-width={448}
        shadow-mapSize-height={448}
        shadow-camera-near={1}
        shadow-camera-far={30}
        shadow-camera-left={-10}
        shadow-camera-right={20}
        shadow-camera-top={10}
        shadow-camera-bottom={-10}
        shadow-bias={-0.005}
      />
    </>
  );
}

// New component to handle position updates inside the Canvas

// // Update the RoverPositionUpdater to also track rotation
// function RoverPositionUpdater({ roverRef, onPositionUpdate, onRotationUpdate }: {
//   roverRef: any,
//   onPositionUpdate: any,
//   onRotationUpdate: any
// }) {
//   const lastUpdateTime = useRef(0);
//   const updateInterval = 300; // Update every 100ms instead of every frame

//   useFrame(() => {
//     const now = Date.now();
//     if (roverRef.current && now - lastUpdateTime.current > updateInterval) {
//       const { x, y, z } = roverRef.current.translation();
//       const rotation = roverRef.current.rotation();
//       onPositionUpdate({ x, y, z });
//       onRotationUpdate(rotation);
//       lastUpdateTime.current = now;
//     }
//   });
//   return null;
// }


// function DirectionIndicator({ currentPosition, roverRotation }: {
//   currentPosition: { x: number, y: number, z: number },
//   roverRotation: any
// }) {
//   // Calculate distance
//   const distance = Math.sqrt(
//     Math.pow(targetPosition.x - currentPosition.x, 2) +
//     Math.pow(targetPosition.z - currentPosition.z, 2)
//   );

//   // Calculate angle to target relative to world coordinates (corrected for Three.js coordinate system)
//   const targetAngle = Math.atan2(
//     targetPosition.x - currentPosition.x,  // Swapped x and z
//     targetPosition.z - currentPosition.z   // This gives us the correct world angle
//   );

//   // Get rover's current facing direction (Y rotation from quaternion)
//   let roverAngle = 0;
//   if (roverRotation) {
//     // Convert quaternion to Euler angle (Y rotation) - corrected formula
//     const { x, y, z, w } = roverRotation;
//     roverAngle = Math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + z * z));
//   }

//   // Calculate relative angle (target direction relative to rover's facing direction)
//   let relativeAngle = (targetAngle - roverAngle) * (180 / Math.PI);

//   // Normalize to -180 to 180 degrees
//   while (relativeAngle > 180) relativeAngle -= 360;
//   while (relativeAngle < -180) relativeAngle += 360;

//   // Invert the angle to match the UI coordinate system
//   relativeAngle = -relativeAngle;

//   return (
//     <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-black/70 backdrop-blur-md border border-white/20 text-white px-4 py-2 rounded-lg shadow-lg">
//       <div className="flex items-center gap-3">
//         {/* Direction Arrow - rotates relative to rover's facing direction */}
//         <div
//           className="w-6 h-6 flex items-center justify-center"
//           style={{ transform: `rotate(${relativeAngle}deg)` }}
//         >
//           <div className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[20px] border-l-transparent border-r-transparent border-b-green-400"></div>
//         </div>

//         {/* Distance Info */}
//         <div className="flex flex-col text-xs">
//           <span className="text-green-400 font-semibold">Target Location</span>
//           <span className="font-mono">{distance.toFixed(1)}m remaining</span>
//         </div>

//         {/* Relative Direction */}
//         {/* <div className="text-xs opacity-75">
//           {Math.abs(relativeAngle) < 15 ? 'Forward' : 
//            relativeAngle > 0 ? `Left ${Math.abs(relativeAngle).toFixed(0)}°` : 
//            `Right ${Math.abs(relativeAngle).toFixed(0)}°`}
//         </div> */}
//       </div>
//     </div>
//   );
// }

// Update the RoverPositionUpdater to use refs and avoid frequent setState calls
function RoverPositionUpdater({ roverRef, onPositionUpdate, onRotationUpdate }: {
  roverRef: any,
  onPositionUpdate: any,
  onRotationUpdate: any
}) {
  const lastUpdateTime = useRef(0);
  const currentPosition = useRef({ x: 0, y: 0, z: 0 });
  const currentRotation = useRef(null);
  const updateInterval = 100; // Update UI every 500ms instead of every frame

  useFrame(() => {
    const now = performance.now(); // Use performance.now() for better precision
    
    if (roverRef.current && now - lastUpdateTime.current > updateInterval) {
      // Use try-catch to prevent errors from affecting physics
      try {
        const { x, y, z } = roverRef.current.translation();
        const rotation = roverRef.current.rotation();
        
        onPositionUpdate({ x, y, z });
        onRotationUpdate(rotation);
        lastUpdateTime.current = now;
      } catch (error) {
        // Silently handle any errors to prevent physics interruption
        console.warn('Position update error:', error);
      }
    }
  });
  
  return null;
}

// Also update DirectionIndicator to be more performant
function DirectionIndicator({ currentPosition, roverRotation }: {
  currentPosition: { x: number, y: number, z: number },
  roverRotation: any
}) {
  // Memoize expensive calculations
  const distance = useMemo(() => Math.sqrt(
    Math.pow(targetPosition.x - currentPosition.x, 2) +
    Math.pow(targetPosition.z - currentPosition.z, 2)
  ), [currentPosition.x, currentPosition.z]);

  const relativeAngle = useMemo(() => {
    // Calculate angle to target relative to world coordinates
    const targetAngle = Math.atan2(
      targetPosition.x - currentPosition.x,
      targetPosition.z - currentPosition.z
    );

    // Get rover's current facing direction (Y rotation from quaternion)
    let roverAngle = 0;
    if (roverRotation) {
      const { x, y, z, w } = roverRotation;
      roverAngle = Math.atan2(2 * (w * y + x * z), 1 - 2 * (y * y + z * z));
    }

    // Calculate relative angle
    let angle = (targetAngle - roverAngle) * (180 / Math.PI);

    // Normalize to -180 to 180 degrees
    while (angle > 180) angle -= 360;
    while (angle < -180) angle += 360;

    // Invert the angle to match the UI coordinate system
    return -angle;
  }, [currentPosition.x, currentPosition.z, roverRotation]);

  return (
    <div className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-black/70 backdrop-blur-md border border-white/20 text-white px-4 py-2 rounded-lg shadow-lg">
      <div className="flex items-center gap-3">
        {/* Direction Arrow - rotates relative to rover's facing direction */}
        <div
          className="w-6 h-6 flex items-center justify-center"
          style={{ transform: `rotate(${relativeAngle}deg)` }}
        >
          <div className="w-0 h-0 border-l-[5px] border-r-[5px] border-b-[20px] border-l-transparent border-r-transparent border-b-green-400"></div>
        </div>

        {/* Distance Info */}
        <div className="flex flex-col text-xs">
          <span className="text-green-400 font-semibold">Target Location</span>
          <span className="font-mono">{distance.toFixed(1)}m remaining</span>
          <span>Moving 100 times faster than actual speed</span>
        </div>

        {/* Relative Direction */}
        <div className="text-xs opacity-75">
          {Math.abs(relativeAngle) < 15 ? 'Forward' : 
           relativeAngle > 0 ? `Left ${Math.abs(relativeAngle).toFixed(0)}°` : 
           `Right ${Math.abs(relativeAngle).toFixed(0)}°`}
        </div>
      </div>
    </div>
  );
}


export default function Home() {

  const roverRef = useRef<RapierRigidBody | null>(null);
  const [roverPosition, setRoverPosition] = useState({ x: 0, y: 0, z: 0 });
  const [roverRotation, setRoverRotation] = useState(null);
  const [isMapOpen, setIsMapOpen] = useState(false);

  return (
    <div className="w-screen h-screen bg-amber-100">
      <KeyboardControls
        map={[
          { name: "ArrowUp", keys: ["ArrowUp"] },
          { name: "ArrowDown", keys: ["ArrowDown"] },
          { name: "ArrowLeft", keys: ["ArrowLeft"] },
          { name: "ArrowRight", keys: ["ArrowRight"] },
          { name: "w", keys: ["w"] },
          { name: "s", keys: ["s"] },
          { name: "a", keys: ["a"] },
          { name: "d", keys: ["d"] },
          { name: "q", keys: ["q"] },
          { name: "e", keys: ["e"] },
          { name: "i", keys: ["i"] },
          { name: "k", keys: ["k"] },
          { name: "j", keys: ["j"] },
          { name: "l", keys: ["l"] },
        ]}
      >

        <Canvas
          shadows
          camera={{ position: [5, 5, 5], fov: 50 }}
          dpr={[0.5, 1]}
          performance={{ min: 0.5 }} // Add performance settings
          gl={{
            antialias: true, // Disable for better performance
            powerPreference: "high-performance"
          }}
        >
          <fog attach="fog" args={['#fef3c6', 10, 200]} />
          <ambientLight intensity={0.7} color={'#e1c79d'} />

          <SunLight targetRef={roverRef} />

          <Text3D
            font="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/fonts/helvetiker_regular.typeface.json" // **You need to provide the font file.**
            size={.5}
            height={0.1}
            curveSegments={12}
            position={[-3.3, 4.5, 2.7]} // Position it slightly above the ground
            rotation={[0, Math.PI / 2, 0]}
          // castShadow
          >
            LANDING SPOT
            <meshStandardMaterial color="white" transparent={true} opacity={.5} />
          </Text3D>

          <Text3D
            font="https://raw.githubusercontent.com/mrdoob/three.js/dev/examples/fonts/helvetiker_regular.typeface.json" // **You need to provide the font file.**
            size={.5}
            height={0.1}
            curveSegments={12}
            position={[88, 4.5, -32]} // Position it slightly above the ground
            rotation={[0, Math.PI / 2, 0]}
          // castShadow
          >
            SAMPLE 8, 9
            <meshStandardMaterial color="white" transparent={true} opacity={.5} />
          </Text3D>

          <Physics gravity={[0, -9.8, 0]}>
            {/* -3.728 */}
            <Ground />
            <RoverController ref={roverRef} />
            <RoverPositionUpdater
              roverRef={roverRef}
              onPositionUpdate={setRoverPosition}
              onRotationUpdate={setRoverRotation}
            />
            {/* <OrbitControls /> */}
          </Physics>
        </Canvas>

        {/* Add Direction Indicator */}
        {/* Updated Direction Indicator with rover rotation */}
        <DirectionIndicator
          currentPosition={roverPosition}
          roverRotation={roverRotation}
        />

        <div className="absolute bottom-4 flex flex-row items-center justify-center gap-2 w-full">
          {/* map button */}
          <Button className="bg-white/10 backdrop-blur-md border border-white/20 text-white hover:bg-white/20 transition-all duration-300 shadow-lg"
            onClick={() => setIsMapOpen(!isMapOpen)}
          >
            <MapPin className="animate-bounce" />
          </Button>
          <ChatBar />
        </div>
        {/* Overlay UI to display the position */}
        <div className="absolute top-0 left-0">
          <Info />
        </div>

        {/* current location */}
        {/* <div className="absolute top-2 right-2 h-fit w-fit text-xs p-2 rounded-lg text-white bg-black/50 bg-opacity-50 font-mono flex items-center gap-3">
          <p>X:{roverPosition.x.toFixed(2)}</p>
          <p>Y:{roverPosition.y.toFixed(2)}</p>
          <p>Z:{roverPosition.z.toFixed(2)}</p>
        </div> */}


        {/* map */}
        <div className={`absolute inset-0 bg-black/50 backdrop-blur-3xl bg-opacity-70 z-10 transition-opacity duration-300 ${isMapOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'}`} onClick={() => setIsMapOpen(false)}></div>
        <div hidden={!isMapOpen} className="absolute scale-[.75] top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-all duration-300 z-50">
          <div className="h-[699px] w-[1322px] relative">
            {/* rover icon */}
            <span className={`fixed font-bold text-xl`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                top: `${505 - roverPosition.z / 10}px`,
                left: `${1210 - roverPosition.x / 10}px`,
              }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <Image src={'/rover-pointer.png'} height={50} width={50} alt="rover" />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Your are here</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 1 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 3.4}px`,
                top: `${505 + 95.2}px`,
              }}

              onClick={() => { targetPosition = { x: 34, y: 0, z: -952 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 1</p>
                </TooltipContent>
              </Tooltip>
            </span>


            {/* sample 2 3 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 394 / 10}px`,
                top: `${505 + 781 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 394, y: 0, z: -781 }; }}
            >

              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 2, 3</p>
                </TooltipContent>
              </Tooltip>
            </span>

            {/* sample 4 5 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 473 / 10}px`,
                top: `${505 + 597 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 473, y: 0, z: -597 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 4, 5</p>
                </TooltipContent>
              </Tooltip>
            </span>

            {/* sample 6 7 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 573 / 10}px`,
                top: `${505 + 674 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 573, y: 0, z: -674 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 6, 7</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 8 & 9 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 88 / 10}px`,
                top: `${505 + 32 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 88, y: 0, z: -32 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 8, 9</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 10 11 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 2632 / 10}px`,
                top: `${505 - 828 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 2632, y: 0, z: 828 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 10, 11</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 12 & 13 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 2648 / 10}px`,
                top: `${505 - 802 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 2648, y: 0, z: 802 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 12, 13</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 14 & 15 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 2904 / 10}px`,
                top: `${505 - 347 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 2904, y: 0, z: 347 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 14, 15</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 16*/}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 3039 / 10}px`,
                top: `${505 - 527 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 3039, y: 0, z: 527 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 16</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 17 & 18 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 2919 / 10}px`,
                top: `${505 - 395 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 2919, y: 0, z: 395 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 17, 18</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 19 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 3926 / 10}px`,
                top: `${505 - 1463 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 3926, y: 0, z: 1463 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 19</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 20 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 4850 / 10}px`,
                top: `${505 - 2177 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 4850, y: 0, z: 2177 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 20</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 21 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 5302 / 10}px`,
                top: `${505 - 2229 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 5302, y: 0, z: 2229 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 21</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 23 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 5876 / 10}px`,
                top: `${505 - 2212 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 5876, y: 0, z: 2212 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 23</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 24 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 7163 / 10}px`,
                top: `${505 - 2663 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 7163, y: 0, z: 2663 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 24</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 25 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 8539 / 10}px`,
                top: `${505 - 3024 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 8539, y: 0, z: 3024 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 25</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 26 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 10909 / 10}px`,
                top: `${505 - 939 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 10909, y: 0, z: 939 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 26</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 27 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 10932 / 10}px`,
                top: `${505 - 953 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 10932, y: 0, z: 953 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 27</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 28 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 11298 / 10}px`,
                top: `${505 - 1014 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 11298, y: 0, z: 1014 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 28</p>
                </TooltipContent>
              </Tooltip>

            </span>


            {/* sample 29 */}
            <span className={`fixed text-blue-200 text-xl hover:scale-105 transition-all duration-200 font-bold`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                left: `${1210 - 11327 / 10}px`,
                top: `${505 - 1044 / 10}px`,
              }}

              onClick={() => { targetPosition = { x: 11327, y: 0, z: 1044 }; }}
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <MapPin />
                </TooltipTrigger>
                <TooltipContent>
                  <p>Sample 29</p>
                </TooltipContent>
              </Tooltip>

            </span>

            {/* target icon */}
            <span className={`fixed text-green-500 text-3xl font-bold animate-transition transition-all duration-200`}

              style={{
                // Perform arithmetic directly on the 'top' and 'left' style properties.
                top: `${505 - targetPosition.z / 10}px`,
                left: `${1210 - targetPosition.x / 10}px`,
              }}
            >
              <MapPin />
            </span>

            <Image src={'/map.webp'} height={699} width={1322} alt="map" />
          </div>
        </div>

        {/* keyboard controls */}
        {/* <div className="absolute bottom-2 left-2 flex flex-col items-center justify-center gap-2 opacity-30 scale-75">
          <div className="bg-black w-10 h-10 flex items-center justify-center text-white"><MoveUp /></div>
          <div className="flex items-center gap-2">
            <div className="bg-black w-10 h-10 flex items-center justify-center text-white"><MoveLeft /></div>
            <div className="bg-black w-10 h-10 flex items-center justify-center text-white"><MoveDown /></div>
            <div className="bg-black w-10 h-10 flex items-center justify-center text-white"><MoveRight /></div>
          </div>
        </div> */}

      </KeyboardControls>
    </div>
  );
}



