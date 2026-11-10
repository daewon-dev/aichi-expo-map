import Foundation
import Vision
import AppKit
let path = CommandLine.arguments[1]
let img = NSImage(contentsOfFile: path)!
var rect = NSRect(origin: .zero, size: img.size)
let cg = img.cgImage(forProposedRect: &rect, context: nil, hints: nil)!
let W = Double(cg.width), H = Double(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
req.minimumTextHeight = 0.004
req.customWords = []
let h = VNImageRequestHandler(cgImage: cg, options: [:])
try h.perform([req])
var out: [[String: Any]] = []
for o in req.results ?? [] {
  guard let c = o.topCandidates(1).first else { continue }
  let b = o.boundingBox
  out.append(["t": c.string, "x": b.minX*W, "y": (1-b.maxY)*H, "w": b.width*W, "h": b.height*H, "c": c.confidence])
}
let d = try JSONSerialization.data(withJSONObject: out)
FileManager.default.createFile(atPath: CommandLine.arguments[2], contents: d)
print(out.count, W, H)
