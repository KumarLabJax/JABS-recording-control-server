"""
this utilty file contains functions related to processing a device's state as
and determining if we need to reply with a command for the device client
"""
import json
from flask_restplus import abort

import src.app.model as model
from src.utils.exceptions import LTMSControlServiceException
from src.utils.logging import get_module_logger

LOGGER = get_module_logger()


def get_device_response(device, client_data):
    # get session ID included in message if present
    client_session = client_data.get('session_id')

    # has the device been assigned to a recording session?
    if device.session_id:

        device_session_status = model.DeviceRecordingStatus.get(device,
                                                                device.recording_session)

        # this is an extra sanity check
        if not device_session_status:
            # device has a session id associated with it in the database,
            # but it doesn't have a corresponding row in
            # DeviceRecordingStatus
            LOGGER.error("device doesn't have corresponding "
                         f"DeviceRecordingStatus for session {device.session_id}")
            try:
                device.clear_session()
            except LTMSControlServiceException:
                # for now pass, it should try again next heartbeat
                pass
            return '', 204

        # device doesn't know it's been assigned to the session yet
        if not client_session:
            if device_session_status.status == model.DeviceRecordingStatus.Status.PENDING:
                # we were waiting to hear from device to tell it to start
                return {
                           'command_name': "START",
                           'parameters': json.dumps({
                               'session_id': device.session_id,
                               'duration': device.recording_session.duration,
                               'fragment_hourly': device.recording_session.fragment_hourly,
                               'file_prefix': device_session_status.file_prefix,
                               'target_fps': device.recording_session.target_fps,
                               'apply_filter': device.recording_session.apply_filter
                           })
                       }, 200
            elif device_session_status.status == model.DeviceRecordingStatus.Status.CANCELED:
                # device appears to have successfully canceled, clear its
                # active session so it is available to be included in a
                # new session
                try:
                    device.clear_session()
                except LTMSControlServiceException:
                    # for now pass, it should try again next heartbeat
                    pass
                return '', 204
            else:
                # device is unexpectedly idle after it had previously
                # joined the recording session.
                try:
                    device_session_status.update_status(
                        model.DeviceRecordingStatus.Status.FAILED,
                        "device unexpectedly left recording session"
                    )
                    device.clear_session()
                except LTMSControlServiceException:
                    # couldn't update the status for some reason
                    # don't treat this as fatal, we'll try again next time
                    pass

        else:
            # device already knows it is part of a session
            # update its state accordingly

            # extra sanity check
            if device.session_id != client_session:
                # device and server are confused.
                # tell device to stop what it is doing
                return {'command_name': "STOP"}, 200

            if not client_data['sensor_status']['camera']['recording']:
                # device is no longer recording

                # check to see if there was an error
                err_msg = client_data.get('err_msg')

                try:
                    if err_msg:
                        # handle error case
                        device_session_status.update_status(
                            model.DeviceRecordingStatus.Status.FAILED,
                            err_msg
                        )
                    else:
                        # no error, this means the device finished recording
                        duration = client_data['sensor_status']['camera'].get(
                            'duration', 0)
                        device_session_status.update_recording_time(
                            duration)
                        if device_session_status.status == model.DeviceRecordingStatus.Status.RECORDING:
                            device_session_status.update_status(
                                model.DeviceRecordingStatus.Status.COMPLETE
                            )

                    device.clear_session()
                    return {'command_name': "COMPLETE"}, 200

                except LTMSControlServiceException:
                    # couldn't update the device for some reason
                    # don't treat this as fatal. we will try again next time
                    # device sends us a status update
                    pass

            elif device_session_status.status == model.DeviceRecordingStatus.Status.CANCELED:
                # we have a cancel request for this device,
                # tell it to stop recording
                return {'command_name': "STOP"}, 200
            elif device_session_status.status == model.DeviceRecordingStatus.Status.RECORDING:
                # device is recording, update our recording status with
                # the current recording duration
                try:
                    device_session_status.update_recording_time(
                        client_data['sensor_status']['camera']['duration'])
                except LTMSControlServiceException:
                    # couldn't update the device time for some reason
                    # don't treat this as fatal.
                    pass
            elif device_session_status.status == model.DeviceRecordingStatus.Status.PENDING:
                # device is sending first update after joining the session
                try:
                    device.join_session(
                        device_session_status.session)
                except LTMSControlServiceException as err:
                    abort(400, f"error joining session {err}")

                try:
                    device_session_status.update_recording_time(
                        client_data['sensor_status']['camera']['duration'])
                except LTMSControlServiceException:
                    # couldn't update the device time for some reason
                    # don't treat this as fatal.
                    pass
    return '', 204
