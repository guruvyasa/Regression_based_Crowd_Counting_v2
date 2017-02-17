from tiah import FileManager as files
from tiah import tools as tools
from src.Prepare import Prepare
from src.PrepareGIST import PrepareGIST
from os import getcwd, chdir
import cv2, pyGPs, pickle
# from src.Direct_Feature import run_SURF_v4,run_FAST_v4
import src.Direct_Feature as directs
import src.Indirect_Feature as indirects
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from tiah.tools import graph
from src.others import knr
from sklearn.decomposition import PCA
from tiah import ImageHandler as images
import time
from tiah import tools as tools


class worker:
    def __init__(self):

        P = range(2, 7)
        D = range(2, 7)
        # d1~d6: using pn
        # d7: only E using p3
        # d8: only E using p5
        # d9: only E using p6

        chdir('..')
        for pv, dv in zip(P, D):
            self.run_pets_case(pv, dv)
            # self.run_pets_case(5, 7)
            # self.run_gist_case()

    def run_pets_case(self, pv, dv):

        self.param_version = pv  # 4
        self.feature_version = 5
        # self.feature_version = 4 # for d1~d6
        self.dir_version = dv  # 1  # directory differs parameter

        self.bpath = files.mkdir(getcwd(), 'S1L1')
        self.res_path = files.mkdir(self.bpath, 'res' + str(self.dir_version))
        self.param_path = files.mkdir(self.bpath, 'params_v' + str(self.param_version))
        self.graph_path = files.mkdir(self.res_path, 'graphs')
        self.model_path = files.mkdir(self.res_path, 'models')
        self.prepare = Prepare(self.bpath, self.res_path, self.param_version)
        self.prepare.init_pets()
        # prepare.test_background_subtractor()
        self.FEATURE1357 = 'featureset1357.npy'
        self.FEATURE1359 = 'featureset1359.npy'
        self.COUNTGT1357 = 'c_groundtruth1357.npy'
        self.COUNTGT1359 = 'c_groundtruth1359.npy'

        print 'Current Param Version: ', self.param_version
        print 'Current Directory Version: ', self.dir_version

        a1357, b1357, a1359, b1359, weight, gt1357, gt1359 = self.prepare.prepare()
        param1357 = self.prepare.param1357
        param1359 = self.prepare.param1359
        fg1357 = a1357[0]
        dpcolor1357 = b1357[0]
        dpmask1357 = b1357[1]

        fg1359 = a1359[0]
        dpcolor1359 = b1359[0]
        dpmask1359 = b1359[1]
        # v2: only K
        # v3: only K E T
        # v3: K E T P S S2

        # import segm as segm
        # segm.testing(fg1357,dpcolor1357,dpmask1357,param1357,self.res_path)
        # quit()



        # dplist = self.draw_shapes(self.prepare,fg1357,dpcolor1357,dpmask1357)
        # tmp_path = files.mkdir(self.param_path, 'rect_contour')
        # images.write_imgs(dplist,tmp_path,'rc')
        # images.write_video(dplist,8, tmp_path,'rc')
        # return 1

        E = 1
        K = 1
        P = 1
        S = 1
        T = 1
        feature_version = {'E': E, 'K': K, 'P': P, 'S': S, 'T': T}

        self.create_feature_set(fg1357, dpcolor1357, weight, feature_version, param1357, gt1357,
                                self.COUNTGT1357, '1357')
        self.create_feature_set(fg1359, dpcolor1359, weight, feature_version, param1359, gt1359,
                                self.COUNTGT1359, '1359')
        # features1357 = np.load(self.param_path + '/v' + str(self.feature_version) + '_' + self.FEATURE1357)
        # features1359 = np.load(self.param_path + '/v' + str(self.feature_version) + '_' + self.FEATURE1359)


        print 'data1357: ', fg1357.shape, dpcolor1357.shape, len(dpmask1357)
        print 'data1359: ', fg1359.shape, dpcolor1359.shape, len(dpmask1359)
        # K,E,T,P,S,S2
        length = len(dpcolor1359)

        comb1357, labels, groundtruth1357 = self.make_combination(feature_version, '1357')
        comb1359, labels, groundtruth1359 = self.make_combination(feature_version, '1359')

        self.dowork(comb1357, comb1359, labels, dpcolor1359[1:length - 1], fg1359[1:length - 1],
                    groundtruth1357, groundtruth1359)

    def load_feature_set(self, version):
        np.load(self.param_path + '/feature_P_v' + str(version['P']))

    def make_combination(self, version, flag):
        # labels = ['E']
        # labels = ['E', 'K',  'T', 'P', 'S', 'KE', 'KT', 'KP', 'KS', 'ET', 'EP', 'ES', 'KPS']
        labels = ['E', 'K', 'T', 'P', 'S']
        feature_path = files.mkdir(self.param_path, flag)
        print 'loading features from ', feature_path
        E = np.load(feature_path + '/feature_E_v' + str(version['E']) + '.npy')  # np.array(features[0])
        K = np.load(feature_path + '/feature_K_v' + str(version['K']) + '.npy')  # np.array(features[1])
        T = np.load(feature_path + '/feature_T_v' + str(version['T']) + '.npy')  # np.array(features[2])
        P = np.load(feature_path + '/feature_P_v' + str(version['P']) + '.npy')  # np.array(features[3])
        S = np.load(feature_path + '/feature_S_v' + str(version['S']) + '.npy')  # np.array(features[4])
        # S2 = np.load(self.param_path + '/feature_P_v' + str(version['P'])) #np.array(features[5])

        KE = self.make_dual_form(K, E)
        KT = self.make_dual_form(K, T)
        KP = self.make_dual_form(K, P)
        KS = self.make_dual_form(K, S)

        ET = self.make_dual_form(E, T)
        EP = self.make_dual_form(E, P)
        ES = self.make_dual_form(E, S)

        KPS = self.make_triple_form(K, P, S)
        KES = self.make_triple_form(K, E, S)

        # combinations = [E, K, T, P, S, KE, KS, KES]
        # combinations = [E, K, T, P, S, KE, KT, KP, KS, ET, EP, ES, KPS]
        combinations = [E, K, T, P, S]
        if flag == '1357':
            groundtruth = np.load(feature_path + '/' + self.COUNTGT1357)
        else:
            groundtruth = np.load(feature_path + '/' + self.COUNTGT1359)

        return combinations, labels, groundtruth

    def make_dual_form(self, A, B):
        newone = []
        for frame1, frame2 in zip(A, B):
            frame = []

            for a, b in zip(frame1, frame2):
                frame.append(np.hstack((a, b)))

            newone.append(frame)

        return np.array(newone)

    def make_triple_form(self, A, B, C):
        newone = []
        for frame1, frame2, frame3 in zip(A, B, C):
            frame = []

            for a, b, c in zip(frame1, frame2, frame3):
                frame.append(np.hstack((a, b, c)))

            newone.append(frame)

        return np.array(newone)

    def draw_shapes(self, prepare, fg1357, dp1357, dpmask1357):
        #####################################
        # DO NOT DELETE
        xml1357 = 'PETS2009-S1L1-1'
        GT1357 = 'xml_groundtruth1357.npy'

        contour_tree = []
        rect_tree = []
        for fg in fg1357:
            list_rect, list_contours = self.segmentation_blob(fg, prepare.param1357)
            contour_tree.append(list_contours)
            rect_tree.append(list_rect)

        dp_count_tree, count_tree = prepare.create_count_groundtruth(fg1357, xml1357, 'adf', 1357)

        dplist = []
        for frame_count, frame_rect, frame_contour, dpcolor, dpmask in zip(count_tree, rect_tree, contour_tree, dp1357,
                                                                           dpmask1357):
            for s, c in zip(frame_rect, frame_count):
                cv2.rectangle(dpcolor, (s[0], s[2]), (s[1], s[3]), tools.orange, 1)
                cv2.rectangle(dpmask, (s[0], s[2]), (s[1], s[3]), tools.orange, 1)
                cv2.putText(dpcolor, str(c), (s[0], s[2]), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, tools.blue, 2)
                cv2.putText(dpmask, str(c), (s[0], s[2]), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, tools.blue, 2)

            # cv2.drawContours(dpcolor,frame_contour,-1, tools.red,-1)
            # cv2.drawContours(dpmask,frame_contour,-1, tools.red)


            cv2.drawContours(dpcolor, frame_contour, -1, tools.green, 2)
            cv2.drawContours(dpmask, frame_contour, -1, tools.green, 2)

            dplist.append(np.hstack((dpcolor, dpmask)))
            # cv2.imshow('1', np.hstack((dpcolor, dpmask)))
            # cv2.waitKey(0)
        return dplist

    def gt_test(self, prepare, fg1357, dp1357, dpmask1357):
        #####################################
        # DO NOT DELETE
        xml1357 = 'PETS2009-S1L1-1'
        GT1357 = 'xml_groundtruth1357.npy'

        seg_tree = []
        for fg in fg1357:
            list_rect, list_contours = self.segmentation_blob(fg, prepare.param1357)
            seg_tree.append(list_rect)

        dp_count_tree, count_tree = prepare.create_count_groundtruth(fg1357, xml1357, 'adf', 1357)

        for frame_count, frame_seg, dpcolor, dpmask in zip(dp_count_tree, seg_tree, dp1357, dpmask1357):
            for i in range(len(frame_seg)):
                s = frame_seg[i]
                cv2.rectangle(dpcolor, (s[0], s[2]), (s[1], s[3]), tools.green, 1)
                cv2.rectangle(dpmask, (s[0], s[2]), (s[1], s[3]), tools.green, 1)

                abc = frame_count[i]
                for gt in abc:
                    cv2.rectangle(dpcolor, (gt[0], gt[2]), (gt[1], gt[3]), tools.red, 1)
                    cv2.rectangle(dpmask, (gt[0], gt[2]), (gt[1], gt[3]), tools.red, 1)

                cv2.imshow('1', np.hstack((dpcolor, dpmask)))
                cv2.waitKey(0)

    def test_drawing_segmentation(self, fgset, dp_color, fname):

        a = []
        for f in fgset:
            frame_rect, frame_contour = self.segmentation_blob(f, [10, 10, 0])
            a.append(frame_rect)

        b = self.draw_segmentation(dp_color, a)

        images.write_video(b, 30, self.res_path, fname + '_segmented')

    def draw_segmentation(self, frame_set, seg_set):

        results = []
        for i in range(len(frame_set)):
            frame = frame_set[i].copy()
            frame_seg = seg_set[i]

            for s in frame_seg:
                cv2.rectangle(frame, (s[0], s[2]), (s[1], s[3]), tools.green, 1)
            results.append(frame)

        return results

    def test3d(self, X, Y, Z):

        plot_type = ['b', 'g', 'r', 'c', 'm', 'y']

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')

        ax.scatter(X, Y, Z, c='b', marker='o')
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')

        plt.show()

    def pca_test(self, features, version, label):
        groundtruth = np.load(self.param_path + '/v' + str(version) + '_' + self.GT)

        _trainX = np.concatenate(features[0:features.shape[0]:2])
        _trainY = np.concatenate(groundtruth[0:groundtruth.size:2])
        pca = PCA(n_components=2)
        X = pca.fit_transform(_trainX)
        self.test3d(X[:, 0], X[:, 1], _trainY)

    def dowork(self, features1357, features1359, labels, dpcolors, fgset, groundtruth1357, groundtruth1359):

        # groundtruth = self.read_count_groundtruth()
        # groundtruth = groundtruth[1:len(groundtruth) - 1]
        # print 'custom gt len: ', len(groundtruth)
        # print 'custom gt concat ', np.concatenate(groundtruth).shape

        print '1357 case'
        print 'frame: ', features1357[0].shape, ' Groundntruth: ', groundtruth1357.shape
        print 'feature X: ', np.concatenate(features1357[0]).shape, ' label Y: ', np.concatenate(groundtruth1357).shape

        print '1359 case'
        print 'frame: ', features1359[0].shape, ' Groundntruth: ', groundtruth1359.shape
        print 'feature X: ', np.concatenate(features1359[0]).shape, ' label Y: ', np.concatenate(groundtruth1359).shape

        MAE_frame = []
        MAE_feature = []
        for i in range(len(labels)):
            train_feature = features1357[i]
            test_feature = features1359[i]

            graph_name = 'case1'  # l1v1 auto gt, l1v2 auto gt
            _trainX = np.concatenate(train_feature)
            _trainY = np.concatenate(groundtruth1357)
            testX = test_feature
            testY = groundtruth1359
            pred, sum_pred, gt, gt_sum = self.train_model_test_plot(_trainX, _trainY, testX, testY, graph_name,
                                                                    labels[i])

            MAE_frame.append(np.mean(np.abs(np.array(sum_pred)-np.array(gt_sum))))
            MAE_feature.append(np.mean(np.abs(np.array(pred)-np.array(gt))))


            #####################################################################


            # graph_name = 'case2' # l1v1 custom_gt , l1v2 auto_gt
            # groundtruth = self.read_count_groundtruth()
            # _trainX = np.concatenate(train_feature)
            # _trainY = np.concatenate(groundtruth)
            # testX = test_feature
            # testY = groundtruth1359
            # self.train_model_test_plot(_trainX, _trainY, testX, testY, graph_name, labels[i])


            #####################################################################


            # graph_name = 'case3' # l1v1 odd auto gt, l1v1 event auto gt
            # _trainX = np.concatenate(train_feature[0:train_feature.shape[0]:2])
            # _trainY = np.concatenate(groundtruth1357[0:groundtruth1357.size:2])
            # testX = train_feature[1:train_feature.shape[0]:2]
            # testY = groundtruth1357[1:groundtruth1357.size:2]
            # self.train_model_test_plot(_trainX, _trainY, testX, testY, graph_name, labels[i])


            #####################################################################
            # l1v1 odd custom_gt
            # l1v1 even custom_gt

            # graph_name = 'case4'
            # _trainX = np.concatenate(train_feature[0: train_feature.size:2])
            # _trainY = np.concatenate(groundtruth[0: len(groundtruth):2])
            # testX = train_feature[1:train_feature.size:2]
            # testY = groundtruth[1:len(groundtruth):2]
            # self.train_model_test_plot(_trainX, _trainY, testX, testY, graph_name, labels[i])

            #####################################################################






            # self.plot_knr(knr_results[0], knr_results[1], knr_results[2], knr_results[3], labels[i], graph_name, vpath)
            # self.make_video(dpcolors, fgset, gpr_results, 'gpr_' + labels[i], self.prepare.param1359)
            # self.make_video(dpcolors, fgset, knr_results, 'knr_' + labels[i], self.prepare.param1359)

    def train_model_test_plot(self, _trainX, _trainY, testX, testY, graph_name, label):
        print '_trainX: ', _trainX.shape, ' _trainY: ', _trainY.shape
        print 'testX: ', testX.shape, ' testY: ', np.array(testY).shape

        gpr_results = self.train_model_and_test(_trainX, _trainY, testX, testY, label, 'model',
                                                '1357-1359',
                                                self.model_path)  # each result set contains [pred, sum_pred, gt, gt_sum]

        self.plot_gpr(gpr_results[0], gpr_results[1], gpr_results[2], gpr_results[3], label, graph_name,
                      self.graph_path)
        return gpr_results

    def train_model_and_test(self, _trainX, _trainY, testX, testY, label, mname, fname, model_path):
        """
        Learns GPR and KNR model from given training set and test on test set.

        Here, training set consists of every odd feature and test set consists of every training set is equal to test set.

        :param _trainX:
        :param _trainY:
        :param testX:
        :param testY:
        :param label:
        :param mname:
        :param fname:
        :param model_path:
        :return:
        """

        trainX, trainY = self.exclude_label(_trainX, _trainY, c=0)

        print '_trainX.shape: ', trainX.shape, ', _trainY.shape: ', trainY.shape

        PYGPR = 'gpr_' + label + '_' + mname

        if files.isExist(model_path, PYGPR):
            gprmodel = self.loadf(model_path, PYGPR)

        else:
            print 'Learning GPR model'
            gprmodel = pyGPs.GPR()
            gprmodel.getPosterior(trainX, trainY)
            gprmodel.optimize(trainX, trainY)
            self.savef(model_path, PYGPR, gprmodel)

        # gpred, gsum_pred, ggt, ggt_sum = self.prediction_gpr_model(gprmodel,testX,[])
        # kpred, ksum_pred, kgt, kgt_sum = self.prediction_gpr_model(knrmodel,testX,[])

        gpr_result = self.prediction_gpr_model(gprmodel, testX, testY)

        return gpr_result


        # self.plot_gpr(gprmodel,testX,testY,label,fname)
        # self.plot_knr(knrmodel,testX,testY,label,fname)

    def make_video(self, colordp, fgset, result, fname, param):

        # pred, sum_pred, gt, gt_sum
        Y_pred_frame = result[0]
        print 'Y_pred_frame: ', len(Y_pred_frame), 'fgset: ', len(fgset)
        videopath = files.mkdir(self.res_path, 'prediction_videos')
        imgset = []
        for i in range(len(fgset)):
            rect, cont = self.segmentation_blob(fgset[i], param)
            tmp = colordp[i].copy()

            pred = Y_pred_frame[i]
            # print 'rect size: ' , len(rect), 'frame_pred: ' , len(pred)
            # gt =  groundtruth[i]
            for j in range(len(rect)):
                r = rect[j]
                cv2.rectangle(tmp, (r[0], r[2]), (r[1], r[3]), tools.green, 2)
                msg_pred = '#:' + str(tools.int2round(pred[j]))
                cv2.putText(tmp, msg_pred, (r[0], r[2]), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, tools.blue, 2)
                # msg_gt = 'GT: '+str(gt[j])
                # cv2.putText(tmp, msg_gt, (r[0]+10,r[2]),cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.0, tools.red)
            imgset.append(tmp)
        # images.display_img(imgset, 300)
        images.write_video(imgset, 20, videopath, fname)

    def prediction_gpr_model(self, model, testX, testY):
        pred = np.array([])
        sum_pred = []

        gt = np.array([])
        gt_sum = []
        for y in testY:
            gt = np.hstack((gt, y))
            gt_sum.append(sum(y))

        for x in testX:
            ym, ys2, fm, fs2, lp = model.predict(np.array(x))
            ym = ym.reshape(ym.size)
            pred = np.hstack((pred, ym))
            sum_pred.append(sum(ym))

        return pred, sum_pred, gt, gt_sum

    def prediction_knr_model(self, model, testX, testY):
        pred = np.array([])
        sum_pred = []

        gt = np.array([])
        gt_sum = []
        for y in testY:
            gt = np.hstack((gt, y))
            gt_sum.append(sum(y))

        for x in testX:
            ym = model.predict(x)
            pred = np.hstack((pred, ym))
            sum_pred.append(sum(ym))

        return pred, sum_pred, gt, gt_sum

    def get_feature_by_label(self, _X, _Y, c):
        X = []
        Y = []

        for i in range(len(_X)):
            if _Y[i] != c:
                X.append(_X[i])
                Y.append(_Y[i])

        return np.array(X), np.array(Y)

    def plot_knr(self, Y_pred, Y_sum_pred, Y_label, Y_sum_label, label, fname, vpath):
        """

        :param Y_sum_pred: frame_prediction
        :param Y_pred: feature_prediction
        :param Y_sum_label: frame_gt
        :param Y_label: feature_gt
        :param label:
        :param fname:
        :return:
        """

        sxp = np.linspace(0, len(Y_sum_pred), len(Y_sum_pred))
        xp = np.linspace(0, len(Y_pred), len(Y_pred))

        plt.cla()
        plt.clf()
        plt.subplot(211)
        l1, = plt.plot(sxp, Y_sum_pred, 'b^', label='prediction')
        l2, = plt.plot(sxp, Y_sum_label, 'g.', label='groundtruth')
        l3, = plt.plot(sxp, abs(np.array(Y_sum_pred) - np.array(Y_sum_label)), 'r-', label='difference')
        plt.legend(handles=[l1, l2, l3], loc='best')
        plt.ylim([0, 40])
        plt.title('KNR estimation on frame ' + label)
        plt.xlabel('frame index')
        plt.ylabel('# people')

        plt.subplot(212)
        l4, = plt.plot(xp, Y_pred, 'b^', label='prediction')
        l5, = plt.plot(xp, Y_label, 'g.', label='groundtruth')
        l6, = plt.plot(xp, abs(np.array(Y_pred) - np.array(Y_label)), 'r*', label='difference')
        plt.legend(handles=[l4, l5, l6], loc='best')
        plt.ylim([0, 9])
        plt.title('KNR estimation on feature ' + label)
        plt.xlabel('frame index')
        plt.ylabel('# people')
        plt.tight_layout()
        plt.savefig(vpath + '/' + fname + '_knr_' + label + '.png')

        # plt.show()

    def plot_gpr(self, Y_pred, Y_sum_pred, Y_label, Y_sum_label, label, fname, vpath):
        """

        :param Y_sum_pred: frame_prediction
        :param Y_pred: feature_prediction
        :param Y_sum_label: frame_gt
        :param Y_label: feature_gt
        :param label:
        :param fname:
        :return:
        """
        print 'feature pred ', len(Y_pred), ' == ', len(Y_label)
        print 'frame pred ', len(Y_sum_pred), ' == ', len(Y_sum_label)

        sxp = np.linspace(0, len(Y_sum_pred), len(Y_sum_pred))
        xp = np.linspace(0, len(Y_pred), len(Y_pred))

        plt.cla()
        plt.clf()
        plt.subplot(211)
        l1, = plt.plot(sxp, Y_sum_pred, 'b^', label='prediction')
        l2, = plt.plot(sxp, Y_sum_label, 'g.', label='groundtruth')
        l3, = plt.plot(sxp, abs(np.array(Y_sum_pred) - np.array(Y_sum_label)), 'r-', label='error')
        plt.legend(handles=[l1, l2, l3], loc='best')
        plt.ylim([0, 40])
        plt.title('GPR estimation on frame ' + label)
        plt.xlabel('frame index')
        plt.ylabel('# people')

        plt.subplot(212)
        l4, = plt.plot(xp, Y_pred, 'b^', label='prediction')
        l5, = plt.plot(xp, Y_label, 'g.', label='groundtruth')
        l6, = plt.plot(xp, abs(np.array(Y_pred) - np.array(Y_label)), 'r*', label='error')
        plt.legend(handles=[l4, l5, l6], loc='best')
        plt.title('GPR estimation on feature ' + label)
        plt.ylim([0, 9])
        plt.xlabel('feature index')
        plt.ylabel('# people')
        plt.tight_layout()
        plt.savefig(vpath + '/' + fname + '_gpr_' + label + '.png')
        # plt.show()

    def create_feature_set(self, fgset, dpcolor, weight, version, param, givengt, gname, flag):
        """
        Extracts features (e.g., K, S, P, E, T) from each image.

        K.shape = n_frames * 2
        S.shape = n_frames * 2
        P.shape = n_frames * 4
        E.shape = n_frames * 6
        T.shape = n_frames * 4

        :param fgset:
        :param dpcolor:
        :param weight:
        :param version:
        :param param:
        :param givengt:
        :param gname:
        :return:
        """
        print 'making feature set sequence, in ', self.param_path

        feature_path = files.mkdir(self.param_path, flag)

        contours_tree = []
        rectangles_tree = []
        groundtruth_tree = givengt  # self.read_count_groundtruth()

        for f in fgset:
            rect, cont = self.segmentation_blob(f, param)
            contours_tree.append(cont)
            rectangles_tree.append(rect)

        size = len(fgset)

        if not files.isExist(feature_path, gname):
            groundtruth = []
            for i in range(1, size - 1):
                groundtruth.append(groundtruth_tree[i])
            np.save(feature_path + '/' + gname, groundtruth)

        if not files.isExist(feature_path, 'feature_E_v' + str(version['E']) + '.npy'):

            E = []
            for i in range(1, size - 1):
                e = directs.get_canny_edges(dpcolor[i], weight, rectangles_tree[i], self.dir_version)
                E.append(e)
            np.save(feature_path + '/feature_E_v' + str(version['E']), E)

        if not files.isExist(feature_path, 'feature_K_v' + str(version['K']) + '.npy'):
            print 'K not exist'
            K = []
            for i in range(1, size - 1):
                ks = directs.run_SURF_v4(dpcolor[i], weight, rectangles_tree[i])
                kf = directs.run_FAST_v4(dpcolor[i], weight, rectangles_tree[i])
                K.append(np.vstack((ks, kf)).T)
            np.save(feature_path + '/feature_K_v' + str(version['K']), K)
        else:
            print 'K exist'

        if not files.isExist(feature_path, 'feature_T_v' + str(version['T']) + '.npy'):
            T = []
            for i in range(1, size - 1):
                t = directs.get_texture_T(dpcolor[i - 1:i + 2, :, :], rectangles_tree[i])
                T.append(t)
            np.save(feature_path + '/feature_T_v' + str(version['T']), T)

        if not files.isExist(feature_path, 'feature_S_v' + str(version['S']) + '.npy'):
            S = []
            for i in range(1, size - 1):
                l = indirects.get_size_L(fgset[i], weight, contours_tree[i])
                s = indirects.get_size_S(fgset[i], weight, contours_tree[i])
                S.append(np.vstack((s, l)).T)
            np.save(feature_path + '/feature_S_v' + str(version['S']), S)

        if not files.isExist(feature_path, 'feature_P_v' + str(version['P']) + '.npy'):
            P = []
            for i in range(1, size - 1):
                p = indirects.get_shape_P(fgset[i], weight, contours_tree[i])
                P.append(p)
            np.save(feature_path + '/feature_P_v' + str(version['P']), P)

    def read_count_groundtruth(self):
        """
        reads text file which contains groundtruth.
        :return:
        """

        lines = files.read_text(self.bpath, 'count_gt')
        res = []
        for line in lines:
            tmp = line.split(',')
            tmp = tools.int2round(tmp)
            res.append(tmp)
        return res

    def exclude_label(self, _X, _Y, c):
        X = []
        Y = []

        for i in range(len(_X)):
            if _Y[i] != c:
                X.append(_X[i])
                Y.append(_Y[i])
        return np.array(X), np.array(Y)

    def segmentation_blob(self, given_fg, param):
        """
        Find segmenations in given frame.
        :param fg:
        :return: list of rectangle(x1,x2,y1,y2)
        """
        list_rect = []
        list_contours = []

        minw = param[0]
        minh = param[1]
        miny = param[2]

        # contours, heiarchy = cv2.findContours(given_frame, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours, heiarchy = cv2.findContours(given_fg, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)  # check here

        if len(contours) != 0:  # if contour exists
            for i in range((len(contours))):
                if len(contours[i]) > 100:  # thresholding n_point of contours
                    rect = cv2.boundingRect(contours[i])  # find fitted_rectangle to given contour.

                    w = rect[2]
                    h = rect[3]
                    ux = rect[0]
                    uy = rect[1]
                    # segment should be larger than the minimum size of object in groundtruth.
                    # and object should be located in inside of ROI.
                    if w > minw and h > minh and uy + h > miny:
                        reform = (ux, ux + w, uy, uy + h)
                        list_rect.append(reform)
                        list_contours.append(contours[i])

        return list_rect, list_contours

    def savef(self, path, fname, given):
        with open(path + '/' + fname, 'w') as f:
            pickle.dump(given, f)

    def loadf(self, path, fname):
        with open(path + '/' + fname) as f:
            return pickle.load(f)


worker()
# if __name__ == '__main__':
#     print "Main Starts", '--------------------------' * 5
#     worker()
#     print "Main Ends", '--------------------------' * 5
