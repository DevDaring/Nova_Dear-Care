Windows PowerShell
Copyright (C) Microsoft Corporation. All rights reserved.

Try the new cross-platform PowerShell https://aka.ms/pscore6

PS C:\Users\Debz> cd D:\Contest\Nova_Dear-Care\flutter_app
PS D:\Contest\Nova_Dear-Care\flutter_app>
PS D:\Contest\Nova_Dear-Care\flutter_app> # 1. Clean Flutter build artifacts
PS D:\Contest\Nova_Dear-Care\flutter_app> flutter clean
Deleting build...                                                1,091ms
Deleting .dart_tool...                                              16ms
Deleting ephemeral...                                                1ms
Deleting Generated.xcconfig...                                       2ms
Deleting flutter_export_environment.sh...                            0ms
Deleting ephemeral...                                                1ms
Deleting ephemeral...                                                0ms
Deleting .flutter-plugins-dependencies...                            0ms
PS D:\Contest\Nova_Dear-Care\flutter_app> Get-Process -Name "kotlin*" -ErrorAction SilentlyContinue | Stop-Process -Force
PS D:\Contest\Nova_Dear-Care\flutter_app>
PS D:\Contest\Nova_Dear-Care\flutter_app> # 3. Delete corrupted build cache manually (if it still exists)
PS D:\Contest\Nova_Dear-Care\flutter_app> Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
PS D:\Contest\Nova_Dear-Care\flutter_app>
PS D:\Contest\Nova_Dear-Care\flutter_app> # 4. Get dependencies fresh
PS D:\Contest\Nova_Dear-Care\flutter_app> flutter pub get
Resolving dependencies... (1.4s)
Downloading packages...
  characters 1.4.0 (1.4.1 available)
  fl_chart 0.68.0 (1.2.0 available)
  flutter_lints 3.0.2 (6.0.0 available)
  flutter_local_notifications 17.2.4 (21.0.0 available)
  flutter_local_notifications_linux 4.0.1 (8.0.0 available)
  flutter_local_notifications_platform_interface 7.2.0 (11.0.0 available)
  geolocator 11.1.0 (14.0.2 available)
  geolocator_android 4.6.2 (5.0.2 available)
  geolocator_web 3.0.0 (4.1.3 available)
  intl 0.19.0 (0.20.2 available)
  lints 3.0.0 (6.1.0 available)
  matcher 0.12.17 (0.12.19 available)
  material_color_utilities 0.11.1 (0.13.0 available)
  meta 1.17.0 (1.18.1 available)
  sensors_plus 4.0.2 (7.0.0 available)
  sensors_plus_platform_interface 1.2.0 (2.0.1 available)
  test_api 0.7.7 (0.7.10 available)
  timezone 0.9.4 (0.11.0 available)
Got dependencies!
18 packages have newer versions incompatible with dependency constraints.
Try `flutter pub outdated` for more information.
Building with plugins requires symlink support.

Please enable Developer Mode in your system settings. Run
  start ms-settings:developers
to open settings.
PS D:\Contest\Nova_Dear-Care\flutter_app>
PS D:\Contest\Nova_Dear-Care\flutter_app> # 5. Run again
PS D:\Contest\Nova_Dear-Care\flutter_app> flutter run
Launching lib\main.dart on sdk gphone64 x86 64 in debug mode...
warning: [options] source value 8 is obsolete and will be removed in a future release
warning: [options] target value 8 is obsolete and will be removed in a future release
warning: [options] To suppress warnings about obsolete options, use -Xlint:-options.
3 warnings
warning: [options] source value 8 is obsolete and will be removed in a future release
warning: [options] target value 8 is obsolete and will be removed in a future release
warning: [options] To suppress warnings about obsolete options, use -Xlint:-options.
3 warnings
e: Daemon compilation failed: null
java.lang.Exception
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:69)
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:65)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemon(GradleKotlinCompilerWork.kt:240)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemonOrFallbackImpl(GradleKotlinCompilerWork.kt:159)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.run(GradleKotlinCompilerWork.kt:111)
        at org.jetbrains.kotlin.compilerRunner.GradleCompilerRunnerWithWorkers$GradleKotlinCompilerWorkAction.execute(GradleCompilerRunnerWithWorkers.kt:74)
        at org.gradle.workers.internal.DefaultWorkerServer.execute(DefaultWorkerServer.java:63)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:66)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:62)
        at org.gradle.internal.classloader.ClassLoaderUtils.executeInClassloader(ClassLoaderUtils.java:100)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.lambda$execute$0(NoIsolationWorkerFactory.java:62)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:44)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:41)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:210)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:205)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:67)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:167)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:54)
        at org.gradle.workers.internal.AbstractWorker.executeWrappedInBuildOperation(AbstractWorker.java:41)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.execute(NoIsolationWorkerFactory.java:59)
        at org.gradle.workers.internal.DefaultWorkerExecutor.lambda$submitWork$0(DefaultWorkerExecutor.java:174)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runExecution(DefaultConditionalExecutionQueue.java:194)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.access$700(DefaultConditionalExecutionQueue.java:127)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner$1.run(DefaultConditionalExecutionQueue.java:169)
        at org.gradle.internal.Factories$1.create(Factories.java:31)
        at org.gradle.internal.work.DefaultWorkerLeaseService.withLocks(DefaultWorkerLeaseService.java:263)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:127)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:132)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runBatch(DefaultConditionalExecutionQueue.java:164)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.run(DefaultConditionalExecutionQueue.java:133)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Unknown Source)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
        at org.gradle.internal.concurrent.AbstractManagedExecutor$1.run(AbstractManagedExecutor.java:48)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(Unknown Source)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(Unknown Source)
        at java.base/java.lang.Thread.run(Unknown Source)
Caused by: java.lang.AssertionError: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:218)
        at org.jetbrains.kotlin.incremental.IncrementalCachesManager.close(IncrementalCachesManager.kt:55)
        at kotlin.io.CloseableKt.closeFinally(Closeable.kt:46)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compileNonIncrementally(IncrementalCompilerRunner.kt:293)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compile(IncrementalCompilerRunner.kt:128)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.execIncrementalCompiler(CompileServiceImpl.kt:684)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.access$execIncrementalCompiler(CompileServiceImpl.kt:94)
        at org.jetbrains.kotlin.daemon.CompileServiceImpl.compile(CompileServiceImpl.kt:1810)
        at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(Unknown Source)
        at java.base/java.lang.reflect.Method.invoke(Unknown Source)
        at java.rmi/sun.rmi.server.UnicastServerRef.dispatch(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport.serviceCall(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport.handleMessages(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run0(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.lambda$run$0(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run(Unknown Source)
        ... 3 more
Caused by: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:205)
        ... 22 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 43 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups: id-to-file.tab, file-to-id.tab
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.LookupStorage.close(LookupStorage.kt:155)
                ... 23 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs: source-to-output.tab
                ... 25 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 24 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\pedometer\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more

e: Daemon compilation failed: null
java.lang.Exception
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:69)
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:65)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemon(GradleKotlinCompilerWork.kt:240)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemonOrFallbackImpl(GradleKotlinCompilerWork.kt:159)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.run(GradleKotlinCompilerWork.kt:111)
        at org.jetbrains.kotlin.compilerRunner.GradleCompilerRunnerWithWorkers$GradleKotlinCompilerWorkAction.execute(GradleCompilerRunnerWithWorkers.kt:74)
        at org.gradle.workers.internal.DefaultWorkerServer.execute(DefaultWorkerServer.java:63)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:66)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:62)
        at org.gradle.internal.classloader.ClassLoaderUtils.executeInClassloader(ClassLoaderUtils.java:100)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.lambda$execute$0(NoIsolationWorkerFactory.java:62)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:44)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:41)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:210)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:205)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:67)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:167)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:54)
        at org.gradle.workers.internal.AbstractWorker.executeWrappedInBuildOperation(AbstractWorker.java:41)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.execute(NoIsolationWorkerFactory.java:59)
        at org.gradle.workers.internal.DefaultWorkerExecutor.lambda$submitWork$0(DefaultWorkerExecutor.java:174)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runExecution(DefaultConditionalExecutionQueue.java:194)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.access$700(DefaultConditionalExecutionQueue.java:127)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner$1.run(DefaultConditionalExecutionQueue.java:169)
        at org.gradle.internal.Factories$1.create(Factories.java:31)
        at org.gradle.internal.work.DefaultWorkerLeaseService.withLocks(DefaultWorkerLeaseService.java:263)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:127)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:132)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runBatch(DefaultConditionalExecutionQueue.java:164)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.run(DefaultConditionalExecutionQueue.java:133)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Unknown Source)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
        at org.gradle.internal.concurrent.AbstractManagedExecutor$1.run(AbstractManagedExecutor.java:48)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(Unknown Source)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(Unknown Source)
        at java.base/java.lang.Thread.run(Unknown Source)
Caused by: java.lang.AssertionError: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:218)
        at org.jetbrains.kotlin.incremental.IncrementalCachesManager.close(IncrementalCachesManager.kt:55)
        at kotlin.io.CloseableKt.closeFinally(Closeable.kt:46)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compileNonIncrementally(IncrementalCompilerRunner.kt:293)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compile(IncrementalCompilerRunner.kt:128)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.execIncrementalCompiler(CompileServiceImpl.kt:684)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.access$execIncrementalCompiler(CompileServiceImpl.kt:94)
        at org.jetbrains.kotlin.daemon.CompileServiceImpl.compile(CompileServiceImpl.kt:1810)
        at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(Unknown Source)
        at java.base/java.lang.reflect.Method.invoke(Unknown Source)
        at java.rmi/sun.rmi.server.UnicastServerRef.dispatch(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport.serviceCall(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport.handleMessages(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run0(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.lambda$run$0(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run(Unknown Source)
        ... 3 more
Caused by: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:205)
        ... 22 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 43 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups: id-to-file.tab, file-to-id.tab
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.LookupStorage.close(LookupStorage.kt:155)
                ... 23 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs: source-to-output.tab
                ... 25 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 24 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\sensors_plus\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more

e: Daemon compilation failed: null
java.lang.Exception
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:69)
        at org.jetbrains.kotlin.daemon.common.CompileService$CallResult$Error.get(CompileService.kt:65)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemon(GradleKotlinCompilerWork.kt:240)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.compileWithDaemonOrFallbackImpl(GradleKotlinCompilerWork.kt:159)
        at org.jetbrains.kotlin.compilerRunner.GradleKotlinCompilerWork.run(GradleKotlinCompilerWork.kt:111)
        at org.jetbrains.kotlin.compilerRunner.GradleCompilerRunnerWithWorkers$GradleKotlinCompilerWorkAction.execute(GradleCompilerRunnerWithWorkers.kt:74)
        at org.gradle.workers.internal.DefaultWorkerServer.execute(DefaultWorkerServer.java:63)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:66)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1$1.create(NoIsolationWorkerFactory.java:62)
        at org.gradle.internal.classloader.ClassLoaderUtils.executeInClassloader(ClassLoaderUtils.java:100)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.lambda$execute$0(NoIsolationWorkerFactory.java:62)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:44)
        at org.gradle.workers.internal.AbstractWorker$1.call(AbstractWorker.java:41)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:210)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$CallableBuildOperationWorker.execute(DefaultBuildOperationRunner.java:205)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:67)
        at org.gradle.internal.operations.DefaultBuildOperationRunner$2.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:167)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.execute(DefaultBuildOperationRunner.java:60)
        at org.gradle.internal.operations.DefaultBuildOperationRunner.call(DefaultBuildOperationRunner.java:54)
        at org.gradle.workers.internal.AbstractWorker.executeWrappedInBuildOperation(AbstractWorker.java:41)
        at org.gradle.workers.internal.NoIsolationWorkerFactory$1.execute(NoIsolationWorkerFactory.java:59)
        at org.gradle.workers.internal.DefaultWorkerExecutor.lambda$submitWork$0(DefaultWorkerExecutor.java:174)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runExecution(DefaultConditionalExecutionQueue.java:194)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.access$700(DefaultConditionalExecutionQueue.java:127)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner$1.run(DefaultConditionalExecutionQueue.java:169)
        at org.gradle.internal.Factories$1.create(Factories.java:31)
        at org.gradle.internal.work.DefaultWorkerLeaseService.withLocks(DefaultWorkerLeaseService.java:263)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:127)
        at org.gradle.internal.work.DefaultWorkerLeaseService.runAsWorkerThread(DefaultWorkerLeaseService.java:132)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.runBatch(DefaultConditionalExecutionQueue.java:164)
        at org.gradle.internal.work.DefaultConditionalExecutionQueue$ExecutionRunner.run(DefaultConditionalExecutionQueue.java:133)
        at java.base/java.util.concurrent.Executors$RunnableAdapter.call(Unknown Source)
        at java.base/java.util.concurrent.FutureTask.run(Unknown Source)
        at org.gradle.internal.concurrent.ExecutorPolicy$CatchAndRecordFailures.onExecute(ExecutorPolicy.java:64)
        at org.gradle.internal.concurrent.AbstractManagedExecutor$1.run(AbstractManagedExecutor.java:48)
        at java.base/java.util.concurrent.ThreadPoolExecutor.runWorker(Unknown Source)
        at java.base/java.util.concurrent.ThreadPoolExecutor$Worker.run(Unknown Source)
        at java.base/java.lang.Thread.run(Unknown Source)
Caused by: java.lang.AssertionError: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:218)
        at org.jetbrains.kotlin.incremental.IncrementalCachesManager.close(IncrementalCachesManager.kt:55)
        at kotlin.io.CloseableKt.closeFinally(Closeable.kt:46)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compileNonIncrementally(IncrementalCompilerRunner.kt:293)
        at org.jetbrains.kotlin.incremental.IncrementalCompilerRunner.compile(IncrementalCompilerRunner.kt:128)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.execIncrementalCompiler(CompileServiceImpl.kt:684)
        at org.jetbrains.kotlin.daemon.CompileServiceImplBase.access$execIncrementalCompiler(CompileServiceImpl.kt:94)
        at org.jetbrains.kotlin.daemon.CompileServiceImpl.compile(CompileServiceImpl.kt:1810)
        at java.base/jdk.internal.reflect.DirectMethodHandleAccessor.invoke(Unknown Source)
        at java.base/java.lang.reflect.Method.invoke(Unknown Source)
        at java.rmi/sun.rmi.server.UnicastServerRef.dispatch(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport$1.run(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.Transport.serviceCall(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport.handleMessages(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run0(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.lambda$run$0(Unknown Source)
        at java.base/java.security.AccessController.doPrivileged(Unknown Source)
        at java.rmi/sun.rmi.transport.tcp.TCPTransport$ConnectionHandler.run(Unknown Source)
        ... 3 more
Caused by: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin: class-fq-name-to-source.tab, source-to-classes.tab, internal-name-to-source.tab
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
        at org.jetbrains.kotlin.com.google.common.io.Closer.close(Closer.java:205)
        ... 22 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\class-fq-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 43 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\source-to-classes.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] is already registered
                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                ... 24 more
                Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\jvm\kotlin\internal-name-to-source.tab] registration stack trace
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                        ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups: id-to-file.tab, file-to-id.tab
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:95)
                at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.close(BasicMapsOwner.kt:53)
                at org.jetbrains.kotlin.incremental.LookupStorage.close(LookupStorage.kt:155)
                ... 23 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\id-to-file.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.PersistentStorageWrapper.close(PersistentStorage.kt:124)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 25 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\lookups\file-to-id.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more
        Suppressed: java.lang.Exception: Could not close incremental caches in D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs: source-to-output.tab
                ... 25 more
                Suppressed: java.lang.IllegalStateException: Storage for [D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] is already registered
                        at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:410)
                        at org.jetbrains.kotlin.com.intellij.util.io.PagedFileStorage.<init>(PagedFileStorage.java:72)
                        at org.jetbrains.kotlin.com.intellij.util.io.ResizeableMappedFile.<init>(ResizeableMappedFile.java:68)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentBTreeEnumerator.<init>(PersistentBTreeEnumerator.java:128)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentEnumerator.createDefaultEnumerator(PersistentEnumerator.java:52)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:165)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapImpl.<init>(PersistentMapImpl.java:140)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.buildImplementation(PersistentMapBuilder.java:88)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentMapBuilder.build(PersistentMapBuilder.java:71)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:46)
                        at org.jetbrains.kotlin.com.intellij.util.io.PersistentHashMap.<init>(PersistentHashMap.java:72)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.createMap(LazyStorage.kt:62)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.getStorageOrCreateNew(LazyStorage.kt:59)
                        at org.jetbrains.kotlin.incremental.storage.LazyStorage.set(LazyStorage.kt:80)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.applyChanges(InMemoryStorage.kt:108)
                        at org.jetbrains.kotlin.incremental.storage.AppendableInMemoryStorage.applyChanges(InMemoryStorage.kt:179)
                        at org.jetbrains.kotlin.incremental.storage.InMemoryStorage.close(InMemoryStorage.kt:136)
                        at org.jetbrains.kotlin.incremental.storage.AppendableSetBasicMap.close(BasicMap.kt:157)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner$close$1.invoke(BasicMapsOwner.kt:53)
                        at org.jetbrains.kotlin.incremental.storage.BasicMapsOwner.forEachMapSafe(BasicMapsOwner.kt:87)
                        ... 24 more
                        Suppressed: java.lang.Exception: Storage[D:\Contest\Nova_Dear-Care\flutter_app\build\shared_preferences_android\kotlin\compileDebugKotlin\cacheable\caches-jvm\inputs\source-to-output.tab] registration stack trace
                                at org.jetbrains.kotlin.com.intellij.util.io.FilePageCache.registerPagedFileStorage(FilePageCache.java:437)
                                ... 44 more

Running Gradle task 'assembleDebug'...                             64.8s
√ Built build\app\outputs\flutter-apk\app-debug.apk
Installing build\app\outputs\flutter-apk\app-debug.apk...          920ms
D/FlutterJNI( 4117): Beginning load of flutter...
D/FlutterJNI( 4117): flutter (null) was loaded normally!
I/flutter ( 4117): [IMPORTANT:flutter/shell/platform/android/android_context_gl_impeller.cc(104)] Using the Impeller rendering backend (OpenGLES).
D/FlutterGeolocator( 4117): Attaching Geolocator to activity
D/FlutterGeolocator( 4117): Creating service.
D/FlutterGeolocator( 4117): Binding to location service.
I/flutter ( 4117): [Notification] Initialized
D/FlutterGeolocator( 4117): Geolocator foreground service connected
D/FlutterGeolocator( 4117): Initializing Geolocator services
D/FlutterGeolocator( 4117): Flutter engine connected. Connected engine count 1
Syncing files to device sdk gphone64 x86 64...                   1,417ms

Flutter run key commands.
r Hot reload.
R Hot restart.
h List all available interactive commands.
d Detach (terminate "flutter run" but leave application running).
c Clear the screen
q Quit (terminate the application on the device).

A Dart VM Service on sdk gphone64 x86 64 is available at: http://127.0.0.1:51980/Ev68CnWZtIg=/
The Flutter DevTools debugger and profiler on sdk gphone64 x86 64 is available at:
http://127.0.0.1:51980/Ev68CnWZtIg=/devtools/?uri=ws://127.0.0.1:51980/Ev68CnWZtIg=/ws

══╡ EXCEPTION CAUGHT BY RENDERING LIBRARY ╞═════════════════════════════════════════════════════════
The following assertion was thrown during layout:
A RenderFlex overflowed by 21 pixels on the right.

The relevant error-causing widget was:
  Row Row:file:///D:/Contest/Nova_Dear-Care/flutter_app/lib/widgets/sync_status_badge.dart:42:12

The overflowing RenderFlex has an orientation of Axis.horizontal.
The edge of the RenderFlex that is overflowing has been marked in the rendering with a yellow and
black striped pattern. This is usually caused by the contents being too big for the RenderFlex.
Consider applying a flex factor (e.g. using an Expanded widget) to force the children of the
RenderFlex to fit within the available space instead of being sized to their natural size.
This is considered an error condition because it indicates that there is content that cannot be
seen. If the content is legitimately bigger than the available space, consider clipping it with a
ClipRect widget before putting it in the flex, or using a scrollable container rather than a Flex,
like a ListView.
The specific RenderFlex in question is: RenderFlex#c72f0 OVERFLOWING:
  creator: Row ← SyncStatusBadge ← Padding ← Consumer<HealthProvider> ← IconButtonTheme ←
    ConstrainedBox ← LayoutId-[<_ToolbarSlot.leading>] ← CustomMultiChildLayout ← NavigationToolbar ←
    DefaultTextStyle ← IconTheme ← Builder ← ⋯
  parentData: offset=Offset(16.0, 0.0) (can use size)
  constraints: BoxConstraints(w=40.0, h=56.0)
  size: Size(40.0, 56.0)
  direction: horizontal
  mainAxisAlignment: start
  mainAxisSize: min
  crossAxisAlignment: center
  textDirection: ltr
  verticalDirection: down
  spacing: 0.0
◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤◢◤
════════════════════════════════════════════════════════════════════════════════════════════════════

I/Choreographer( 4117): Skipped 300 frames!  The application may be doing too much work on its main thread.
D/ProfileInstaller( 4117): Installing profile for com.example.fit_u
D/WindowLayoutComponentImpl( 4117): Register WindowLayoutInfoListener on Context=com.example.fit_u.MainActivity@fa81a79, of which baseContext=android.app.ContextImpl@2990c04
D/InsetsController( 4117): hide(ime(), fromIme=false)
I/ImeTracker( 4117): com.example.fit_u:b20b4791: onCancelled at PHASE_CLIENT_ALREADY_HIDDEN
