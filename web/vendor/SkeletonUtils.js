/**
 * SkeletonUtils.js - Three.js Skeleton cloning utility
 * Supports deep cloning of SkinnedMesh hierarchies with independent armatures and bones.
 * Zero external dependencies. Fully offline compatible.
 */

(function () {
  function clone(source) {
    const sourceLookup = new Map();
    const cloneLookup = new Map();

    const cloned = source.clone();

    parallelTraverse(source, cloned, (sourceNode, clonedNode) => {
      sourceLookup.set(clonedNode, sourceNode);
      cloneLookup.set(sourceNode, clonedNode);
    });

    cloned.traverse((node) => {
      if (!node.isSkinnedMesh) return;

      const sourceNode = sourceLookup.get(node);
      const morphTargetDictionary = sourceNode ? sourceNode.morphTargetDictionary : null;
      if (morphTargetDictionary) {
        node.morphTargetDictionary = Object.assign({}, morphTargetDictionary);
      }

      if (sourceNode && sourceNode.skeleton) {
        const sourceBones = sourceNode.skeleton.bones;
        const clonedBones = [];

        for (let i = 0; i < sourceBones.length; i++) {
          const sourceBone = sourceBones[i];
          clonedBones.push(cloneLookup.get(sourceBone) || sourceBone);
        }

        node.bind(
          new THREE.Skeleton(clonedBones, sourceNode.skeleton.boneInverses),
          node.matrixWorld
        );
      }
    });

    return cloned;
  }

  function parallelTraverse(a, b, callback) {
    callback(a, b);
    for (let i = 0; i < a.children.length; i++) {
      if (b.children[i]) {
        parallelTraverse(a.children[i], b.children[i], callback);
      }
    }
  }

  if (typeof THREE !== "undefined") {
    THREE.SkeletonUtils = THREE.SkeletonUtils || {};
    THREE.SkeletonUtils.clone = clone;
    THREE.SkeletonUtils.parallelTraverse = parallelTraverse;
  }

  if (typeof module !== "undefined" && module.exports) {
    module.exports = { clone, parallelTraverse };
  }
})();
