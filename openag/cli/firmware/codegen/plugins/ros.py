from ..base import Plugin

class ROSCommPlugin(Plugin):
    def header_files(self):
        return set(["ros.h", "diagnostic_msgs/DiagnosticStatus.h"])

    def write_declarations(self, f):
        f.writeln("ros::NodeHandle nh;")
        f.writeln("diagnostic_msgs::DiagnosticStatus status_msg;")
        f.writeln(
            'ros::Publisher pub_diagnostics("/diagnostics", &status_msg);'
        )
        for mod_name, mod_info in self.modules.items():
            mod_type = self.module_types[mod_info["type"]]

            # Define publishers for all outputs
            for output_name in mod_type["outputs"]:
                f.writeln(
                    'ros::Publisher {pub_name}('
                        '"{output_topic}", &{msg_name}'
                    ');'.format(
                        pub_name=self.pub_name(mod_name, output_name),
                        output_topic=self.output_topic(mod_name, output_name),
                        msg_name=self.msg_name(mod_name, output_name)
                    )
                )

            # Define callbacks and subscribers for all inputs
            for input_name, input_info in mod_type["inputs"].items():
                cls_name = "::".join(input_info["type"].split("/"))
                arguments = "const {cls_name} &msg".format(cls_name=cls_name)
                callback_name = self.callback_name(mod_name, input_name)
                with f._function("void", callback_name, arguments):
                    f.writeln("{mod_name}.set_{input_name}(msg);".format(
                        mod_name=mod_name, input_name=input_name
                    ))
                f.writeln(
                    'ros::Subscriber<{cls_name}> {sub_name}('
                        '"{input_topic}", {callback_name}'
                    ');'.format(
                        cls_name=cls_name,
                        sub_name=self.sub_name(mod_name, input_name),
                        input_topic=self.input_topic(mod_name, input_name),
                        callback_name=self.callback_name(mod_name, input_name)
                    )
                )

    def setup_plugin(self, f):
        f.writeln("Serial.begin(57600);")
        f.writeln("nh.initNode();")

    def setup_module(self, mod_name, f):
        mod_type = self.module_types[self.modules[mod_name]["type"]]
        for output_name in mod_type["outputs"]:
            f.writeln("nh.advertise({pub_name});".format(
                pub_name=self.pub_name(mod_name, output_name)
            ))
        for input_name in mod_type["inputs"]:
            f.writeln("nh.subscribe({sub_name});".format(
                sub_name=self.sub_name(mod_name, input_name)
            ))

    def update_plugin(self, f):
        f.writeln("nh.spinOnce();")

    def update_module(self, mod_name, f):
        f.writeln("nh.spinOnce();")

    def on_output(self, mod_name, output_name, f):
        f.writeln(
            "{pub_name}.publish(&{msg_name});".format(
                pub_name=self.pub_name(mod_name, output_name),
                msg_name=self.msg_name(mod_name, output_name)
            )
        )

    def read_module_status(self, mod_name, f):
        f.writeln("status_msg.level = {mod_name}.status_level;".format(
            mod_name=mod_name
        ))
        f.writeln('status_msg.name = "{mod_name}";'.format(mod_name=mod_name))
        f.writeln('status_msg.message = {mod_name}.status_msg;'.format(
            mod_name=mod_name
        ))
        f.writeln('status_msg.hardware_id = "none";');
        f.writeln("pub_diagnostics.publish(&status_msg);")

    def pub_name(self, mod_name, output_name):
        return "_".join(["pub", mod_name, output_name])

    def sub_name(self, mod_name, input_name):
        return "_".join(["sub", mod_name, input_name])

    def callback_name(self, mod_name, input_name):
        return "_".join([mod_name, input_name, "callback"])

    def output_topic(self, mod_name, output_name):
        return "/sensors/{mod_name}_{output_name}".format(
            mod_name=mod_name, output_name=output_name
        )

    def input_topic(self, mod_name, input_name):
        return "/actuators/{mod_name}_{input_name}".format(
            mod_name=mod_name, input_name=input_name
        )