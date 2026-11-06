import assert from "node:assert/strict";
import { test } from "node:test";
import { formatAngle, formatPosition, scaleBar, scaleDenominator } from "./readout.ts";

test("緯度と経度を、度と分（小数1桁）で書く", () => {
  assert.equal(formatPosition({ lat: 35.6895, lng: 139.6917 }), "35°41.4′N  139°41.5′E");
  assert.equal(formatPosition({ lat: -33.8688, lng: -70.1 }), "33°52.1′S  070°06.0′W");
  assert.equal(formatAngle(10.99999, "N", "S", 2), "11°00.0′N");
});

test("経度は -180〜180 に戻して書く", () => {
  assert.equal(formatPosition({ lat: 0, lng: 190 }), "00°00.0′N  170°00.0′W");
});

test("縮尺の分母は上から2桁で丸める", () => {
  const denominator = scaleDenominator(35, 5);
  assert.equal(denominator % 10 ** (String(denominator).length - 2), 0);
  assert.ok(scaleDenominator(35, 6) < denominator);
});

test("縮尺の棒は、1・2・5 の 10 の累乗の距離で、最大の長さに収まる", () => {
  const { meters, pixels } = scaleBar(35, 5, 120);
  assert.ok(pixels <= 120);
  assert.match(String(meters), /^[125]0*$/);
});
