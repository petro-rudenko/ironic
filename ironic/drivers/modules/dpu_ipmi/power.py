from ironic.common import states
from ironic.conductor import task_manager
from ironic.drivers.modules import ipmitool
from ironic.drivers import utils as driver_utils


class DpuIpmiPower(ipmitool.IPMIPower):
    state = states.POWER_ON

    def get_supported_power_states(self, task):
        """Get a list of the supported power states.
        Dpu supports only POWER_ON state

        :param task: A TaskManager instance containing the node to act on.
            currently not used.
        :returns: A list with the supported power states defined
                  in :mod:`ironic.common.states`.
        """
        return [states.POWER_ON, states.REBOOT]

    def get_power_state(self, task):
        return self.state

    @task_manager.require_exclusive_lock
    def set_power_state(self, task, power_state, timeout=None):
        driver_info = ipmitool._parse_driver_info(task.node)

        if power_state == states.POWER_ON:
            driver_utils.ensure_next_boot_device(task, driver_info)
            cmd = "chassis power reset"
            ipmitool._exec_ipmitool(driver_info, cmd)
            self.state = states.POWER_ON
        elif power_state == states.POWER_OFF:
            self.state = states.POWER_OFF

    @task_manager.require_exclusive_lock
    def reboot(self, task, timeout=None):
        self.set_power_state(task, states.POWER_ON)