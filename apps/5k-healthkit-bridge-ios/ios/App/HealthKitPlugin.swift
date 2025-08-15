import Foundation
import Capacitor
import HealthKit

@objc(HealthKitPlugin)
public class HealthKitPlugin: CAPPlugin {
    private let healthStore = HKHealthStore()

    @objc func isAvailable(_ call: CAPPluginCall) {
        let available = HKHealthStore.isHealthDataAvailable()
        call.resolve(["available": available])
    }

    @objc func requestAuthorization(_ call: CAPPluginCall) {
        guard HKHealthStore.isHealthDataAvailable() else {
            call.resolve(["granted": false, "error": "Health data not available"]) ; return
        }

        let readIds = call.getArray("read", String.self) ?? []
        let writeIds = call.getArray("write", String.self) ?? []

        let readTypes = Set(readIds.compactMap { HealthKitPlugin.hkQuantityType(from: $0) })
        let writeTypes = Set(writeIds.compactMap { HealthKitPlugin.hkQuantityType(from: $0) })

        healthStore.requestAuthorization(toShare: writeTypes, read: readTypes) { success, error in
            DispatchQueue.main.async {
                if success {
                    call.resolve(["granted": true])
                } else {
                    call.resolve(["granted": false, "error": error?.localizedDescription ?? "unknown"]) 
                }
            }
        }
    }

    @objc func saveWorkout(_ call: CAPPluginCall) {
        guard HKHealthStore.isHealthDataAvailable() else {
            call.resolve(["success": false, "error": "Health data not available"]) ; return
        }
        let activityTypeString = call.getString("activityType") ?? "running"
        let distance = call.getDouble("distanceMeters")
        let calories = call.getDouble("calories")
        let startDateStr = call.getString("startDate") ?? ""
        let endDateStr = call.getString("endDate") ?? ""

        let iso = ISO8601DateFormatter()
        guard let start = iso.date(from: startDateStr), let end = iso.date(from: endDateStr) else {
            call.resolve(["success": false, "error": "Invalid dates"]) ; return
        }

        // Map incoming activity string to HealthKit activity type
        let activity: HKWorkoutActivityType = {
            switch activityTypeString.lowercased() {
            case "walking": return .walking
            case "cycling": return .cycling
            case "hiking": return .hiking
            case "swimming": return .swimming
            default: return .running
            }
        }()
        let metadata: [String: Any] = [:]

        // Safely unwrap optionals for distance and calories (explicit for Xcode)
        let distanceValue: Double = distance ?? 0.0
        let caloriesValue: Double = calories ?? 0.0
        let totalDistance: HKQuantity? = distanceValue != 0.0 ? HKQuantity(unit: HKUnit.meter(), doubleValue: distanceValue) : nil
        let totalEnergy: HKQuantity? = caloriesValue != 0.0 ? HKQuantity(unit: .kilocalorie(), doubleValue: caloriesValue) : nil

        if #available(iOS 17.0, *) {
            // Use HKWorkoutBuilder on iOS 17+ to avoid deprecated initializer warnings
            let config = HKWorkoutConfiguration()
            config.activityType = activity
            let builder = HKWorkoutBuilder(healthStore: healthStore, configuration: config, device: .local())
            builder.beginCollection(withStart: start) { began, error in
                guard began, error == nil else {
                    DispatchQueue.main.async {
                        call.resolve(["success": false, "error": error?.localizedDescription ?? "begin failed"])
                    }
                    return
                }
                builder.endCollection(withEnd: end) { ended, error in
                    guard ended, error == nil else {
                        DispatchQueue.main.async {
                            call.resolve(["success": false, "error": error?.localizedDescription ?? "end failed"])
                        }
                        return
                    }
                    builder.finishWorkout { workout, error in
                        DispatchQueue.main.async {
                            if let _ = workout, error == nil {
                                call.resolve(["success": true])
                            } else {
                                call.resolve(["success": false, "error": error?.localizedDescription ?? "finish failed"]) 
                            }
                        }
                    }
                }
            }
        } else {
            // Fallback for iOS < 17
            let workout = createLegacyWorkout(activity: activity, start: start, end: end, totalEnergy: totalEnergy, totalDistance: totalDistance, metadata: metadata)
            healthStore.save(workout) { success, error in
                DispatchQueue.main.async {
                    if success {
                        call.resolve(["success": true])
                    } else {
                        call.resolve(["success": false, "error": error?.localizedDescription ?? "unknown"]) 
                    }
                }
            }
        }
    }

    @available(iOS, introduced: 9.0, deprecated: 17.0)
    private func createLegacyWorkout(activity: HKWorkoutActivityType, start: Date, end: Date, totalEnergy: HKQuantity?, totalDistance: HKQuantity?, metadata: [String: Any]) -> HKWorkout {
        return HKWorkout(
            activityType: activity,
            start: start,
            end: end,
            workoutEvents: nil,
            totalEnergyBurned: totalEnergy,
            totalDistance: totalDistance,
            metadata: metadata
        )
    }

    private static func hkQuantityType(from identifier: String) -> HKQuantityType? {
        switch identifier {
        case "HKQuantityTypeIdentifierDistanceWalkingRunning":
            return HKObjectType.quantityType(forIdentifier: .distanceWalkingRunning)
        case "HKQuantityTypeIdentifierActiveEnergyBurned":
            return HKObjectType.quantityType(forIdentifier: .activeEnergyBurned)
        default:
            return nil
        }
    }
}
