/*
 * This file is part of the OpenKinect Project. http://www.openkinect.org
 *
 * Copyright (c) 2011 individual OpenKinect contributors. See the CONTRIB file
 * for details.
 *
 * This code is licensed to you under the terms of the Apache License, version
 * 2.0, or, at your option, the terms of the GNU General Public License,
 * version 2.0. See the APACHE20 and GPL2 files for the text of the licenses,
 * or the following URLs:
 * http://www.apache.org/licenses/LICENSE-2.0
 * http://www.gnu.org/licenses/gpl-2.0.txt
 *
 * If you redistribute this file in source form, modified or unmodified, you
 * may:
 *   1) Leave this header intact and distribute it under the same terms,
 *      accompanying it with the APACHE20 and GPL20 files, or
 *   2) Delete the Apache 2.0 clause and accompany it with the GPL2 file, or
 *   3) Delete the GPL v2 clause and accompany it with the APACHE20 file
 * In all cases you must keep the copyright notice intact and include a copy
 * of the CONTRIB file.
 *
 * Binary distributions must follow the binary distribution requirements of
 * either License.
 */


#include <iostream>
#include <sstream>
#include <stdio.h>
#include <signal.h>
#include <math.h>

#include <opencv2/opencv.hpp>

#include <libfreenect2/libfreenect2.hpp>
#include <libfreenect2/frame_listener_impl.h>
#include <libfreenect2/threading.h>
#include <libfreenect2/registration.h>
#include <libfreenect2/packet_pipeline.h>

bool protonect_shutdown = false;

void sigint_handler(int s)
{
  protonect_shutdown = true;
}

std::string tostr(int x)
{
    std::stringstream str;
    str << x;
    return str.str();
}

cv::Mat OpenWarpPerspective(const cv::Mat& _image
  , const cv::Point2f& tl
  , const cv::Point2f& tr
  , const cv::Point2f& br
  , const cv::Point2f& bl)
{
  cv::Point2f source_points[4];
  cv::Point2f dest_points[4];

  source_points[0] = tl;
  source_points[1] = tr;
  source_points[2] = br;
  source_points[3] = bl;

  float widthA = sqrt(pow(br.x - bl.x, 2) + pow(br.y - bl.y, 2));
  float widthB = sqrt(pow(tr.x - tl.x, 2) + pow(tr.y - tl.y, 2));
  int _width;
  if (widthA > widthB) {
    _width = (int)widthA;
  } else {
    _width = (int)widthB;
  }

  float heightA = sqrt(pow(tr.x - br.x, 2) + pow(tr.y - br.y, 2));
  float heightB = sqrt(pow(tl.x - bl.x, 2) + pow(tl.y - bl.y, 2));
  int _height;
  if (heightA > heightB) {
    _height = (int)heightA;
  } else {
    _height = (int)heightB;
  }

  dest_points[0] = cv::Point2f(0,0);
  dest_points[1] = cv::Point2f(_width-1,0);
  dest_points[2] = cv::Point2f(_width-1,_height-1);
  dest_points[3] = cv::Point2f(0,_height-1);

  cv::Mat dst;
  cv::Mat _transform_matrix = cv::getPerspectiveTransform(source_points, dest_points);
  cv::warpPerspective(_image, dst, _transform_matrix, cv::Size(_width, _height));

  return dst;
}

int main(int argc, char *argv[])
{
  std::string program_path(argv[0]);
  size_t executable_name_idx = program_path.rfind("Protonect");

  std::string binpath = "/";

  if(executable_name_idx != std::string::npos)
  {
    binpath = program_path.substr(0, executable_name_idx);
  }

  libfreenect2::Freenect2 freenect2;
  libfreenect2::Freenect2Device *dev = 0;
  libfreenect2::PacketPipeline *pipeline = 0;

  if(freenect2.enumerateDevices() == 0)
  {
    std::cout << "no device connected!" << std::endl;
    return -1;
  }

  std::string serial = freenect2.getDefaultDeviceSerialNumber();
  float threshold = -1;
  float transform_p1x = -1;
  float transform_p1y = -1;
  float transform_p2x = -1;
  float transform_p2y = -1;
  float transform_p3x = -1;
  float transform_p3y = -1;
  float transform_p4x = -1;
  float transform_p4y = -1;
  std::string filename ("test_" );

  for(int argI = 1; argI < argc; ++argI)
  {
    const std::string arg(argv[argI]);

    if(arg == "cpu")
    {
      if(!pipeline)
        pipeline = new libfreenect2::CpuPacketPipeline();
    }
    else if(arg == "gl")
    {
#ifdef LIBFREENECT2_WITH_OPENGL_SUPPORT
      if(!pipeline)
        pipeline = new libfreenect2::OpenGLPacketPipeline();
#else
      std::cout << "OpenGL pipeline is not supported!" << std::endl;
#endif
    }
    else if(arg == "cl")
    {
#ifdef LIBFREENECT2_WITH_OPENCL_SUPPORT
      if(!pipeline)
        pipeline = new libfreenect2::OpenCLPacketPipeline();
#else
      std::cout << "OpenCL pipeline is not supported!" << std::endl;
#endif
    }
    else if (arg == "-t") {
      std::string thresholdString (argv[argI+1]);

      std::istringstream ss(argv[argI+1]);
      if (!(ss >> threshold)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      argI += 1;
    }
    else if (arg == "-p") {
      std::istringstream p1xString (argv[argI+1]);
      std::istringstream p1yString (argv[argI+2]);
      std::istringstream p2xString (argv[argI+3]);
      std::istringstream p2yString (argv[argI+4]);
      std::istringstream p3xString (argv[argI+5]);
      std::istringstream p3yString (argv[argI+6]);
      std::istringstream p4xString (argv[argI+7]);
      std::istringstream p4yString (argv[argI+8]);

      if (!(p1xString >> transform_p1x)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p1yString >> transform_p1y)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p2xString >> transform_p2x)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p2yString >> transform_p2y)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p3xString >> transform_p3x)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p3yString >> transform_p3y)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p4xString >> transform_p4x)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      if (!(p4yString >> transform_p4y)) {
        std::cerr << "Invalid number " << argv[argI+1] << '\n';
      }

      argI += 8;
    }
    else if (arg == "-o") {
      std::string pathString (argv[argI+1]);

      filename = pathString + "/" + filename;
      std::cout << filename << std::endl;

      argI += 1;
    }
    else if(arg.find_first_not_of("0123456789") == std::string::npos) //check if parameter could be a serial number
    {
      serial = arg;
    }
    else
    {
      std::cout << "Unknown argument: " << arg << std::endl;
    }
  }

  if(pipeline)
  {
    dev = freenect2.openDevice(serial, pipeline);
  }
  else
  {
    dev = freenect2.openDevice(serial);
  }

  if(dev == 0)
  {
    std::cout << "failure opening device!" << std::endl;
    return -1;
  }

  signal(SIGINT,sigint_handler);
  protonect_shutdown = false;

  libfreenect2::SyncMultiFrameListener listener(libfreenect2::Frame::Color | libfreenect2::Frame::Ir | libfreenect2::Frame::Depth);
  libfreenect2::FrameMap frames;
  libfreenect2::Frame undistorted(512, 424, 4), registered(512, 424, 4);

  dev->setColorFrameListener(&listener);
  dev->setIrAndDepthFrameListener(&listener);
  dev->start();

  std::cout << "device serial: " << dev->getSerialNumber() << std::endl;
  std::cout << "device firmware: " << dev->getFirmwareVersion() << std::endl;

  libfreenect2::Registration* registration = new libfreenect2::Registration(dev->getIrCameraParams(), dev->getColorCameraParams());

  int i = 0;
  while(!protonect_shutdown)
  {
    listener.waitForNewFrame(frames);
    libfreenect2::Frame *rgb = frames[libfreenect2::Frame::Color];
    libfreenect2::Frame *ir = frames[libfreenect2::Frame::Ir];
    libfreenect2::Frame *depth = frames[libfreenect2::Frame::Depth];

    cv::imshow("rgb", cv::Mat(rgb->height, rgb->width, CV_8UC4, rgb->data));
    //cv::imshow("ir", cv::Mat(ir->height, ir->width, CV_32FC1, ir->data) / 20000.0f);
    //cv::imshow("depth", cv::Mat(depth->height, depth->width, CV_32FC1, depth->data) / 4500.0f);

    registration->apply(rgb, depth, &undistorted, &registered);

    //cv::imshow("undistorted", cv::Mat(undistorted.height, undistorted.width, CV_32FC1, undistorted.data) / 4500.0f);
    //cv::imshow("registered", cv::Mat(registered.height, registered.width, CV_8UC4, registered.data));

    if (i > 10) {
      i = 0;
      for (int j=0; j<=10; j++) {
        std::string jIndex = tostr(j);
        if(remove((filename + jIndex + ".png").c_str()) != 0) {
          perror( "Error deleting file" );
        } else {
          puts( "File successfully deleted" );
        }
      }
    }


    cv::Mat undistortedFrame = cv::Mat(undistorted.height, undistorted.width, CV_32FC1, undistorted.data) / 4500.0f;
    cv::Mat img_bw;
    undistortedFrame.convertTo(img_bw, CV_8UC4, 255);
    cv::Mat thresh;
    if (threshold >= 0) {
      thresh = img_bw > threshold;
    } else {
      thresh = img_bw;
    }

    cv::Mat output;
    if (transform_p1x >= 0) {
      cv::Size output_size = thresh.size();
      std::cout <<
      transform_p1x * (output_size.width-1) << " " << transform_p1y * (output_size.height-1) << " " <<
      transform_p2x * (output_size.width-1) << " " << transform_p2y * (output_size.height-1) << " " <<
      transform_p3x * (output_size.width-1) << " " << transform_p3y * (output_size.height-1) << " " <<
      transform_p4x * (output_size.width-1) << " " << transform_p4y * (output_size.height-1) << std::endl;
      output = OpenWarpPerspective(thresh,
        cv::Point2f(transform_p1x * (output_size.width-1), transform_p1y * (output_size.height-1)),
        cv::Point2f(transform_p2x * (output_size.width-1), transform_p2y * (output_size.height-1)),
        cv::Point2f(transform_p3x * (output_size.width-1), transform_p3y * (output_size.height-1)),
        cv::Point2f(transform_p4x * (output_size.width-1), transform_p4y * (output_size.height-1)));
    } else {
      output = thresh;
    }

    cv::imshow("output", output);

    std::string index = tostr(i);
    cv::imwrite((filename + index + ".png").c_str(), output);
    i += 1;

    int key = cv::waitKey(1000);
    protonect_shutdown = protonect_shutdown || (key > 0 && ((key & 0xFF) == 27)); // shutdown on escape
    if (!protonect_shutdown) {
      std::cout << "key=" << (key & 0xFF) << std::endl;
      if ((key & 0xFF) == 82) {
        threshold += 1;
        std::cout << "increasing threshold" << std::endl;
      } else if ((key & 0xFF) == 83) {
        threshold -= 1;
        std::cout << "decreasing threshold" << std::endl;
      }
    }

    listener.release(frames);
    //libfreenect2::this_thread::sleep_for(libfreenect2::chrono::milliseconds(1000));
  }

  // TODO: restarting ir stream doesn't work!
  // TODO: bad things will happen, if frame listeners are freed before dev->stop() :(
  dev->stop();
  dev->close();

  delete registration;

  return 0;
}
