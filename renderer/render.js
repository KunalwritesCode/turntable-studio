// Loads one glTF model, fits the camera to it, and renders it to a transparent
// PNG data URL at a given turntable angle. Driven by turntable/stages/render.py
// through Playwright; see docs/superpowers/plans/2026-11-25-m2-renderer.md.

import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const params = new URLSearchParams(location.search);
const width = Number(params.get("width")) || 1280;
const height = Number(params.get("height")) || 720;

const canvas = document.getElementById("stage");
const renderer = new THREE.WebGLRenderer({
  canvas,
  alpha: true,
  antialias: true,
  preserveDrawingBuffer: true,
});
renderer.setPixelRatio(1);
renderer.setSize(width, height);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(45, width / height, 0.01, 1000);
scene.add(new THREE.AmbientLight(0xffffff, 1.2));
const key = new THREE.DirectionalLight(0xffffff, 2.0);
key.position.set(1, 2, 3);
scene.add(key);

const turntable = new THREE.Group();
scene.add(turntable);

window.__turntableStatus = "loading";
window.__turntableError = null;

new GLTFLoader().load(
  "model.glb",
  (gltf) => {
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const center = box.getCenter(new THREE.Vector3());
    const sphere = box.getBoundingSphere(new THREE.Sphere());
    gltf.scene.position.sub(center);
    turntable.add(gltf.scene);

    // Fit the bounding sphere within whichever field of view is narrower, so
    // portrait (width < height) renders don't clip the sides.
    const verticalFov = (camera.fov * Math.PI) / 180;
    const horizontalFov = 2 * Math.atan(Math.tan(verticalFov / 2) * camera.aspect);
    const limitingFov = Math.min(verticalFov, horizontalFov);
    const distance = Math.max(sphere.radius / Math.sin(limitingFov / 2), 0.1);
    camera.position.set(0, 0, distance);
    camera.near = distance / 100;
    camera.far = distance * 100;
    camera.updateProjectionMatrix();
    camera.lookAt(0, 0, 0);

    window.__turntableStatus = "ready";
  },
  undefined,
  (error) => {
    window.__turntableError = String((error && error.message) || error);
    window.__turntableStatus = "error";
  },
);

window.renderAtAngle = function renderAtAngle(degrees) {
  turntable.rotation.y = (degrees * Math.PI) / 180;
  renderer.render(scene, camera);
  return canvas.toDataURL("image/png");
};
