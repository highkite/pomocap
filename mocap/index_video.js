import * as tf from "@tensorflow/tfjs-core"
import "@tensorflow/tfjs-converter"
import * as tfjsWasm from "@tensorflow/tfjs-backend-wasm"
import "@tensorflow/tfjs-backend-webgl"
import "@tensorflow/tfjs-backend-webgl"
//import "@tensorflow/tfjs-backend-wasm"
import * as tfnode from "@tensorflow/tfjs-node"
import poseDetection from '@tensorflow-models/pose-detection'
import * as fs from "fs"
import { Canvas } from 'canvas'
import * as tfjs from "@tensorflow/tfjs"

const dirs = fs.readdirSync(process.argv[2])

const model = poseDetection.SupportedModels.PoseNet

function loadImage(path) {
	console.log(`load path: ${path}`)
	let raw_img = fs.readFileSync(path)
	return tfnode.node.decodeImage(raw_img)
}

let tf_images = []
for (let file of dirs) {
	let path = `${process.argv[2]}/${file}`
	tf_images.push(loadImage(path))
}

tf.setBackend("cpu")

async function getPoses(tf_images) {
	let detector = await poseDetection.createDetector(model)
	let pose_data = []
	for(let img of tf_images) {
		pose_data.push(await detector.estimatePoses(img))
	}

	return pose_data

}

getPoses(tf_images).then(data => {
	fs.writeFileSync("./output.json", JSON.stringify(data))
})
