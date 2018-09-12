from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from softlearning.misc.nn import TemplateFunction, feedforward_net_v2
from rllab.core.serializable import Serializable


# tf.enable_eager_execution()


def convnet_preprocessor_template(
        image_size,
        output_size,
        conv_filters=(32, 32),
        conv_kernel_sizes=((5, 5), (5, 5)),
        dense_hidden_layer_sizes=(64, 64),
        data_format='channels_last',
        name="convnet_preprocessor_template",
        create_scope_now_=False,
        *args,
        **kwargs):
    if data_format == 'channels_last':
        H, W, C = image_size
    elif data_format == 'channels_first':
        C, H, W = image_size

    def _fn(x):
        input_images, input_raw = x[..., :H * W * C], x[..., H * W * C:]
        input_layer = tf.reshape(input_images, (-1, H, W, C))

        conv_out = input_layer

        for filters, kernel_size in zip(conv_filters, conv_kernel_sizes):
            conv_out = tf.layers.conv2d(
                inputs=conv_out,
                filters=filters,
                kernel_size=kernel_size,
                padding="SAME",
                activation=tf.nn.relu,
                *args,
                **kwargs)

        spatial_softmax = tf.contrib.layers.spatial_softmax(conv_out)
        flattened = tf.layers.flatten(spatial_softmax)

        concatenated = tf.concat([flattened, input_raw], axis=-1)

        out = feedforward_net_v2(
            inputs=concatenated,
            hidden_layer_sizes=dense_hidden_layer_sizes,
            output_size=output_size,
            activation=tf.nn.relu,
            output_activation=None,
            *args,
            **kwargs)

        return out

    return tf.make_template(name, _fn, create_scope_now_=create_scope_now_)


class ConvnetPreprocessor(TemplateFunction):
    def __init__(self, *args, name='convnet_preprocessor', **kwargs):
        Serializable.quick_init(self, locals())

        super(ConvnetPreprocessor, self).__init__(
            *args, name=name, **kwargs)

    @property
    def template_function(self):
        return convnet_preprocessor_template


# if __name__ == '__main__':
#     batch_size = 1
#     image_size = (32, 32, 3)
#     action_size = 3

#     x1 = tf.placeholder(dtype=tf.float32,
#                         shape=(None, ) + image_size,
#                         name='x1',)
#     x1_num = np.random.normal(size=(batch_size, ) + image_size)
#     x2 = tf.placeholder(dtype=tf.float32,
#                         shape=(None, ) + image_size,
#                         name='x2',)
#     x2_num = np.random.normal(size=(batch_size, ) + image_size)
#     # Pusher 3 dof
#     preprocessor1 = convnet_preprocessor_template(image_size, action_size * 2)
#     preprocessor2 = convnet_preprocessor_template(image_size, action_size * 2)

#     y1 = preprocessor1(x1)
#     y2 = preprocessor1(x1)
#     y3 = preprocessor2(x1)
#     y4 = preprocessor2(x2)

#     assert (preprocessor1.trainable_variables
#             != preprocessor2.trainable_variables)

#     assert (set(tf.trainable_variables()) ==
#             set(preprocessor1.trainable_variables
#                 + preprocessor2.trainable_variables))

#     with tf.Session().as_default():
#         tf.global_variables_initializer().run()
#         assert np.all(tf.equal(y1, y2).eval({x1: x1_num}))
#         assert not np.all(tf.equal(y1, y3).eval({x1: x1_num}))